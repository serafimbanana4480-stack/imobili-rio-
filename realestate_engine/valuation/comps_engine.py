"""Comparable sales engine for valuation.

Implements the industry-standard Comps Method with:
- Multi-factor similarity scoring (area, rooms, location, recency)
- Feature-based price adjustments (garage, renovation, floor, etc.)
- Weighted median calculation for robustness
- Minimum 3 comps requirement for valid estimates
"""
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from loguru import logger

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two coordinates."""
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
        
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ── Adjustment factors (multiplicative % of comparable price) ─────────
# These adjust the comparable's price to estimate what it would be
# if it had the same characteristics as the target property.
# Values are percentages (e.g., 0.08 = +8% of the comp's price).
ADJUSTMENT_FACTORS = {
    "garagem_pct": 0.08,            # Garage adds ~8% of property value
    "garagem_box_pct": 0.10,        # Box garage adds ~10%
    "piscina_pct": 0.10,           # Pool adds ~10%
    "terraco_pct": 0.03,           # Terrace adds ~3%
    "elevador_pct": 0.04,          # Elevator adds ~4%
    "andar_pct_per_floor": 0.01,   # Each extra floor adds ~1%
    "suite_pct": 0.03,             # En-suite adds ~3%
    "vista_premium_add_pct": 0.10,  # Sea/river view: +10%
    "renovacao_premium_pct": 0.12,  # Renovated vs. original: +12%
    "novo_premium_pct": 0.18,       # New vs. used: +18%
    "cert_a_premium_pct": 0.05,     # Energy A/A+: +5%
    "cert_fg_discount_pct": -0.06,  # Energy F/G: -6%
    "quarto_extra_pct": 0.06,      # Each extra bedroom: ~6%
    "wc_extra_pct": 0.02,          # Each extra bathroom: ~2%
}


class CompsEngine:
    """Finds comparable listings and calculates adjusted average price."""

    def __init__(self):
        self.comps_cache: Dict[str, List[Dict]] = {}

    # ── Similarity calculation ──────────────────────────────────────────
    @staticmethod
    def _similarity_score(target: Dict, comp: Dict, distance_m: Optional[float] = None) -> float:
        """Calculate 0-1 similarity score between target and a comparable.

        Factors weighted:
          - Area difference: 30%
          - Room match: 15%
          - Location match (admin): 20%
          - Geographic distance: 20%
          - Recency: 15%
        """
        score = 0.0
        total_weight = 0.0

        # Area similarity (30%)
        t_area = target.get("area_util_m2") or 0
        c_area = comp.get("area_util_m2") or 0
        if t_area > 0 and c_area > 0:
            area_diff = abs(t_area - c_area) / max(t_area, c_area)
            score += (1.0 - min(area_diff, 1.0)) * 0.30
            total_weight += 0.30

        # Room match (15%)
        t_rooms = target.get("quartos") or 0
        c_rooms = comp.get("quartos") or 0
        room_diff = abs(t_rooms - c_rooms)
        if room_diff == 0:
            score += 0.15
        elif room_diff == 1:
            score += 0.09
        else:
            score += 0.0
        total_weight += 0.15

        # Location match (administrative) (20%)
        t_freg = (target.get("freguesia") or "").lower().strip()
        c_freg = (comp.get("freguesia") or "").lower().strip()
        t_conc = (target.get("concelho") or "").lower().strip()
        c_conc = (comp.get("concelho") or "").lower().strip()

        if t_freg and c_freg and t_freg == c_freg:
            score += 0.20  # Same parish = perfect
        elif t_conc and c_conc and t_conc == c_conc:
            score += 0.12  # Same municipality = good
        else:
            score += 0.0
        total_weight += 0.20

        # Geographic distance (20%) — exponential decay with 500m half-life
        if distance_m is not None and distance_m != float('inf'):
            distance_score = math.exp(-distance_m / 500.0)
            score += distance_score * 0.20
            total_weight += 0.20

        # Recency (15%) — newer comps are more relevant
        t_ts = comp.get("scrape_timestamp")
        if t_ts:
            try:
                ts = datetime.fromisoformat(str(t_ts).replace("Z", "+00:00"))
                days_old = (datetime.now(ts.tzinfo) - ts).days
            except Exception:
                days_old = 30
        else:
            days_old = 30

        if days_old < 7:
            score += 0.15
        elif days_old < 30:
            score += 0.10
        elif days_old < 60:
            score += 0.05
        total_weight += 0.15

        return score / total_weight if total_weight > 0 else 0.0

    # ── Price adjustment ────────────────────────────────────────────────
    @staticmethod
    def _adjusted_price(target: Dict, comp: Dict) -> float:
        """Adjust comp's price to estimate target's value.

        Uses multiplicative adjustments (percentage of comp price) so that
        premiums/discounts scale with the local price level.
        """
        comp_price = comp.get("preco_pedido") or 0
        if comp_price <= 0:
            return 0

        adjustment_factor = 1.0

        # Garage adjustment
        comp_garage = comp.get("tem_garagem") or False
        target_garage = target.get("tem_garagem") or False
        if comp_garage and not target_garage:
            adjustment_factor -= ADJUSTMENT_FACTORS["garagem_pct"]
        elif not comp_garage and target_garage:
            adjustment_factor += ADJUSTMENT_FACTORS["garagem_pct"]

        # Room count adjustment
        t_rooms = target.get("quartos") or 0
        c_rooms = comp.get("quartos") or 0
        room_diff = t_rooms - c_rooms
        adjustment_factor += room_diff * ADJUSTMENT_FACTORS["quarto_extra_pct"]

        # Bathroom adjustment
        t_wc = target.get("casas_banho") or 1
        c_wc = comp.get("casas_banho") or 1
        wc_diff = t_wc - c_wc
        adjustment_factor += wc_diff * ADJUSTMENT_FACTORS["wc_extra_pct"]

        # Floor adjustment
        t_floor = target.get("andar") or 0
        c_floor = comp.get("andar") or 0
        floor_diff = t_floor - c_floor
        adjustment_factor += floor_diff * ADJUSTMENT_FACTORS["andar_pct_per_floor"]

        # Condition adjustment (percentage-based)
        t_estado = (target.get("estado") or "").lower()
        c_estado = (comp.get("estado") or "").lower()

        new_states = {"novo", "em_construcao"}
        reno_states = {"renovado", "remodelado"}
        old_states = {"para_recuperar", "ruina"}

        if t_estado in new_states and c_estado not in new_states:
            adjustment_factor += ADJUSTMENT_FACTORS["novo_premium_pct"]
        elif t_estado in reno_states and c_estado not in (new_states | reno_states):
            adjustment_factor += ADJUSTMENT_FACTORS["renovacao_premium_pct"]
        elif t_estado in old_states and c_estado not in old_states:
            adjustment_factor -= ADJUSTMENT_FACTORS["renovacao_premium_pct"]

        # Energy certificate adjustment
        t_cert = (target.get("cert_energetico") or "").upper().strip()
        c_cert = (comp.get("cert_energetico") or "").upper().strip()
        if t_cert in ("A+", "A") and c_cert not in ("A+", "A"):
            adjustment_factor += ADJUSTMENT_FACTORS["cert_a_premium_pct"]
        elif t_cert in ("F", "G") and c_cert not in ("F", "G"):
            adjustment_factor += ADJUSTMENT_FACTORS["cert_fg_discount_pct"]

        # Clamp to avoid negative or wildly inflated prices
        adjustment_factor = max(0.5, min(2.0, adjustment_factor))
        return comp_price * adjustment_factor

    # ── Finding comparables ─────────────────────────────────────────────
    def find_comps_with_tiers(
        self,
        listing: Dict,
        pool: List[Dict],
        area_tolerance: float = 0.25,
        rooms_tolerance: int = 1,
        max_comps: int = 15,
    ) -> Tuple[List[Dict], float]:
        """Find comparable listings using adaptive geographic tiers and return (comps, confidence)."""
        target_area = listing.get("area_util_m2") or 0
        target_rooms = listing.get("quartos") or 0
        target_freg = (listing.get("freguesia") or "").lower().strip()
        target_conc = (listing.get("concelho") or "").lower().strip()
        t_lat = listing.get("lat")
        t_lon = listing.get("lon")

        # 1. Base filtering (Area, Rooms, Price validity)
        valid_pool = []
        for other in pool:
            if other is listing or other.get("source_id") == listing.get("source_id"):
                continue

            price = other.get("preco_pedido")
            area = other.get("area_util_m2") or 0
            rooms = other.get("quartos") or 0

            if not price or price <= 0 or area <= 0:
                continue

            if target_area > 0 and abs(area - target_area) / max(target_area, 1) > area_tolerance:
                continue

            if abs(rooms - target_rooms) > rooms_tolerance:
                continue

            dist = float('inf')
            if t_lat and t_lon and other.get("lat") and other.get("lon"):
                dist = haversine_distance(t_lat, t_lon, other["lat"], other["lon"])

            sim = self._similarity_score(listing, other, dist)
            valid_pool.append({**other, "_similarity": sim, "_distance_m": dist})

        # 2. Adaptive Tiers Evaluation
        # Tier 1: Micro-localization (300m)
        tier_300m = [c for c in valid_pool if c["_distance_m"] <= 300]
        if len(tier_300m) >= 3:
            # Massive similarity boost for being essentially on the same block
            for c in tier_300m: c["_similarity"] += 0.30
            tier_300m.sort(key=lambda c: c.get("_similarity", 0), reverse=True)
            return tier_300m[:max_comps], 0.95
            
        # Tier 2: Neighborhood (500m)
        tier_500m = [c for c in valid_pool if c["_distance_m"] <= 500]
        if len(tier_500m) >= 5:
            for c in tier_500m: c["_similarity"] += 0.20
            tier_500m.sort(key=lambda c: c.get("_similarity", 0), reverse=True)
            return tier_500m[:max_comps], 0.85
            
        # Tier 3: Homogeneous area (1km)
        tier_1km = [c for c in valid_pool if c["_distance_m"] <= 1000]
        if len(tier_1km) >= 8:
            for c in tier_1km: c["_similarity"] += 0.10
            tier_1km.sort(key=lambda c: c.get("_similarity", 0), reverse=True)
            return tier_1km[:max_comps], 0.75

        # Tier 4: Freguesia (Administrative Fallback)
        if target_freg:
            tier_freg = [c for c in valid_pool if (c.get("freguesia") or "").lower().strip() == target_freg]
            if len(tier_freg) >= 10:
                tier_freg.sort(key=lambda c: c.get("_similarity", 0), reverse=True)
                return tier_freg[:max_comps], 0.60
                
        # Tier 5: Concelho (Last resort - heavily penalized)
        if target_conc:
            tier_conc = [c for c in valid_pool if (c.get("concelho") or "").lower().strip() == target_conc]
            if len(tier_conc) >= 15:
                tier_conc.sort(key=lambda c: c.get("_similarity", 0), reverse=True)
                return tier_conc[:max_comps], 0.40
                
        # Reject
        return [], 0.0

    def find_comps(self, listing: Dict, pool: List[Dict], **kwargs) -> List[Dict]:
        """Legacy wrapper returning just comps."""
        comps, _ = self.find_comps_with_tiers(listing, pool, **kwargs)
        return comps

    # ── Value estimation ────────────────────────────────────────────────
    def estimate_value(self, target: Dict, comps: List[Dict]) -> Optional[float]:
        """Estimate value from comparables using weighted adjusted prices."""
        if len(comps) < 3:
            return None

        weighted_prices = []
        weights = []

        for comp in comps:
            adj_price = self._adjusted_price(target, comp)
            if adj_price <= 0:
                continue
            sim = comp.get("_similarity", 0.5)
            weighted_prices.append(adj_price)
            weights.append(sim)

        if not weighted_prices:
            return None

        # Weighted average
        total_weight = sum(weights)
        if total_weight <= 0:
            return statistics.median(weighted_prices)

        weighted_avg = sum(p * w for p, w in zip(weighted_prices, weights)) / total_weight

        # Also calculate median for comparison
        median_price = statistics.median(weighted_prices)

        # Blend weighted average (70%) with median (30%) for robustness
        blended = weighted_avg * 0.7 + median_price * 0.3

        # Cap the Comps estimate at 2x the median comparable price to prevent overvaluation
        # This handles cases where a few expensive outliers skew the average
        if blended > median_price * 2.0:
            blended = median_price * 2.0
            logger.debug(f"Comps estimate capped at 2x median: {blended:,.0f}€")

        logger.debug(
            f"Comps estimate: {blended:,.0f}€ "
            f"(weighted={weighted_avg:,.0f}, median={median_price:,.0f}, "
            f"n={len(weighted_prices)} comps)"
        )
        return blended

    def predict(self, listing: Dict, pool: List[Dict]) -> Tuple[Optional[float], float]:
        """Predict value using comparables, returns (estimated_value, tier_confidence)."""
        comps, conf = self.find_comps_with_tiers(listing, pool)
        if not comps or conf == 0.0:
            logger.debug("Comps: Rejected due to insufficient density in tiers.")
            return None, 0.0
            
        value = self.estimate_value(listing, comps)
        return value, conf

    def get_comps_details(self, listing: Dict, pool: List[Dict]) -> List[Dict]:
        """Return detailed comp information for rationale generation."""
        comps = self.find_comps(listing, pool, max_comps=5)
        details = []
        for c in comps:
            details.append({
                "source_portal": c.get("source_portal"),
                "area_util_m2": c.get("area_util_m2"),
                "quartos": c.get("quartos"),
                "preco_pedido": c.get("preco_pedido"),
                "preco_ajustado": self._adjusted_price(listing, c),
                "freguesia": c.get("freguesia"),
                "similarity": c.get("_similarity", 0),
            })
        return details
