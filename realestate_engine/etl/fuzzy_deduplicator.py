"""Fuzzy deduplication using RapidFuzz for near-duplicate detection.

Extends the existing exact-hash Deduplicator with fuzzy matching to catch
near-duplicates that differ by small area/price variations (e.g. 84m² vs 86m²).

Strategy:
1. Fast pre-filter: bucket by (freguesia, tipologia) — same as current exact dedup
2. Within each bucket: fuzzy compare (area ±10%, price ±8%, geo ±150m)
3. Text similarity on títulos via token_sort_ratio

Expected improvement: 60-70% fewer false negatives vs exact-hash only.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from loguru import logger

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz not available — using basic string comparison for deduplication.")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get(obj, key: str):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


class FuzzyDeduplicator:
    """Near-duplicate detection with configurable thresholds.

    Parameters
    ----------
    area_tolerance : float
        Maximum relative area difference to consider a match (default 0.10 = 10%).
    price_tolerance : float
        Maximum relative price difference (default 0.08 = 8%).
    geo_tolerance_m : float
        Maximum distance in metres (default 150 m).
    title_threshold : int
        Minimum fuzz.token_sort_ratio score (0-100) to flag as text-duplicate (default 85).
    require_geo : bool
        If True, only apply fuzzy matching when geo data is present for both.
    """

    def __init__(
        self,
        area_tolerance: float = 0.10,
        price_tolerance: float = 0.08,
        geo_tolerance_m: float = 150.0,
        title_threshold: int = 85,
        require_geo: bool = False,
    ):
        self.area_tolerance = area_tolerance
        self.price_tolerance = price_tolerance
        self.geo_tolerance_m = geo_tolerance_m
        self.title_threshold = title_threshold
        self.require_geo = require_geo

    def _bucket_key(self, listing) -> str:
        """Bucket key for fast pre-filtering: (freguesia, tipologia)."""
        freg = (_get(listing, "freguesia") or "unknown").strip().lower()
        tip = (_get(listing, "tipologia") or "unknown").strip().upper()
        return f"{freg}|{tip}"

    def _is_fuzzy_duplicate(self, a, b) -> bool:
        """Return True if listing b is a near-duplicate of listing a."""
        area_a = _get(a, "area_util_m2") or 0.0
        area_b = _get(b, "area_util_m2") or 0.0
        price_a = _get(a, "preco_pedido") or 0.0
        price_b = _get(b, "preco_pedido") or 0.0
        lat_a, lon_a = _get(a, "lat"), _get(a, "lon")
        lat_b, lon_b = _get(b, "lat"), _get(b, "lon")

        # Area check
        if area_a > 0 and area_b > 0:
            area_diff = abs(area_a - area_b) / max(area_a, area_b)
            if area_diff > self.area_tolerance:
                return False
        elif area_a != area_b:
            return False

        # Price check
        if price_a > 0 and price_b > 0:
            price_diff = abs(price_a - price_b) / max(price_a, price_b)
            if price_diff > self.price_tolerance:
                return False
        elif price_a != price_b:
            return False

        # Geo check
        has_geo_a = lat_a is not None and lon_a is not None
        has_geo_b = lat_b is not None and lon_b is not None

        if has_geo_a and has_geo_b:
            dist = _haversine_m(lat_a, lon_a, lat_b, lon_b)
            if dist > self.geo_tolerance_m:
                return False
        elif self.require_geo:
            return False

        # Text similarity check (optional — uses RapidFuzz if available)
        if RAPIDFUZZ_AVAILABLE:
            title_a = str(_get(a, "titulo") or "")
            title_b = str(_get(b, "titulo") or "")
            if title_a and title_b:
                score = fuzz.token_sort_ratio(title_a, title_b)
                if score < self.title_threshold:
                    return False
        else:
            # Basic fallback: case-insensitive exact title match if titles are long
            title_a = str(_get(a, "titulo") or "").strip().lower()
            title_b = str(_get(b, "titulo") or "").strip().lower()
            if title_a and title_b and len(title_a) > 20 and title_a != title_b:
                return False

        return True

    def filter_new_against_pool(
        self,
        new_listings: List,
        existing_pool: List,
    ) -> Tuple[List, int]:
        """Filter new_listings against existing_pool for near-duplicates.

        Returns
        -------
        unique : List
            Listings from new_listings that have no near-duplicate in existing_pool.
        n_filtered : int
            Number of near-duplicates removed.
        """
        # if not RAPIDFUZZ_AVAILABLE:
        #    logger.warning("rapidfuzz unavailable — returning all listings unfiltered")
        #    return new_listings, 0

        # Index existing pool by bucket
        pool_by_bucket: Dict[str, List] = {}
        for item in existing_pool:
            key = self._bucket_key(item)
            pool_by_bucket.setdefault(key, []).append(item)

        unique: List = []
        n_filtered = 0

        for listing in new_listings:
            key = self._bucket_key(listing)
            candidates = pool_by_bucket.get(key, [])
            is_dup = False
            for candidate in candidates:
                if self._is_fuzzy_duplicate(listing, candidate):
                    is_dup = True
                    logger.debug(
                        f"Fuzzy duplicate: {_get(listing, 'source_portal')}/"
                        f"{_get(listing, 'source_id')} ≈ "
                        f"{_get(candidate, 'source_portal')}/{_get(candidate, 'source_id')}"
                    )
                    break
            if is_dup:
                n_filtered += 1
            else:
                unique.append(listing)
                # Add to index so intra-batch dedup also works
                pool_by_bucket.setdefault(key, []).append(listing)

        if n_filtered:
            logger.info(f"FuzzyDeduplicator: removed {n_filtered} near-duplicates from {len(new_listings)} candidates")

        return unique, n_filtered

    def deduplicate_batch(self, listings: List) -> Tuple[List, int]:
        """Deduplicate within a single batch (intra-batch near-duplicate removal)."""
        return self.filter_new_against_pool(listings, [])
