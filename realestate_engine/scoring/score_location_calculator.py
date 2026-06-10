"""Location score calculator (25% weight).

Comprehensive Porto-first location scoring with:
- All Porto freguesias with desirability scores
- Grande Porto concelhos coverage
- Matosinhos and Gaia parish-level detail
- Metro proximity scoring
- Walkability (schools, commerce)
- Market trend integration
- Distance to Porto centre (Aliados/Trindade)
"""
import math
from typing import Optional
from loguru import logger


class ScoreLocationCalculator:
    """Calculates location score based on freguesia, metro distance, and POIs."""

    # ── Porto city — freguesia desirability scores ─────────────────────
    # Based on: transaction volume, price trends, demand/supply ratio, amenities
    PORTO_FREGUESIA_SCORES = {
        # Ultra-premium (9.0-10.0)
        "foz do douro": 9.8,
        "nevogilde": 9.6,
        # Premium (8.5-9.0)
        "aldoar": 8.8,
        "massarelos": 9.0,
        "lordelo do ouro": 8.7,
        "boavista": 8.9,
        # High demand (7.5-8.5)
        "cedofeita": 8.3,
        "santo ildefonso": 8.0,
        "vitoria": 8.1,
        "miragaia": 7.8,
        "se": 7.6,
        "sao nicolau": 7.5,
        # Good (6.5-7.5)
        "bonfim": 7.2,
        "ramalde": 7.0,
        "paranhos": 6.8,
        # Developing (5.5-6.5)
        "campanha": 6.0,
    }

    # ── Grande Porto — concelho scores ─────────────────────────────────
    CONCELHO_SCORES = {
        "porto": 8.0,                # City average
        "matosinhos": 7.8,
        "espinho": 7.0,
        "vila nova de gaia": 7.0,
        "povoa de varzim": 6.5,
        "vila do conde": 6.3,
        "maia": 6.0,
        "gondomar": 5.5,
        "valongo": 5.0,
        "trofa": 4.8,
        "santo tirso": 4.5,
        "paredes": 4.3,
        "pacos de ferreira": 4.0,
        "penafiel": 4.0,
        "lousada": 3.8,
        "felgueiras": 3.5,
    }

    # ── Matosinhos — parish scores ─────────────────────────────────────
    MATOSINHOS_FREGUESIAS = {
        "leca da palmeira": 8.5,
        "matosinhos": 8.2,
        "matosinhos sul": 8.3,
        "lavra": 7.8,
        "perafita": 7.5,
        "senhora da hora": 7.2,
        "sao mamede de infesta": 6.8,
        "leca do balio": 6.5,
        "custoias": 6.3,
    }

    # ── Gaia — parish scores ───────────────────────────────────────────
    GAIA_FREGUESIAS = {
        "canidelo": 7.5,
        "mafamude": 7.0,
        "santa marinha": 6.8,
        "valadares": 7.0,
        "arcozelo": 6.8,
        "gulpilhares": 6.5,
        "oliveira do douro": 6.2,
        "vilar de andorinho": 5.8,
        "avintes": 5.5,
        "lever": 5.0,
    }

    @classmethod
    def calculate(
        cls,
        freguesia: Optional[str] = None,
        concelho: Optional[str] = None,
        dist_metro: Optional[float] = None,
        dist_escola: Optional[float] = None,
        dist_comercio: Optional[float] = None,
        ine_tendencia: Optional[float] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> float:
        """Calculate location score (0-10) with multi-factor analysis."""

        # ── 1. Base score from neighbourhood desirability (60% weight) ──
        base_score = cls._neighbourhood_score(freguesia, concelho)

        # ── 2. Metro proximity (15% weight) ─────────────────────────────
        metro_score = cls._metro_score(dist_metro)

        # ── 3. Walkability — schools & commerce (10% weight) ────────────
        walk_score = cls._walkability_score(dist_escola, dist_comercio)

        # ── 4. Market trend momentum (10% weight) ──────────────────────
        trend_score = cls._trend_score(ine_tendencia)

        # ── 5. Centre proximity (5% weight) ─────────────────────────────
        centre_score = cls._centre_proximity_score(lat, lon)

        # Weighted combination
        final = (
            base_score * 0.60 +
            metro_score * 0.15 +
            walk_score * 0.10 +
            trend_score * 0.10 +
            centre_score * 0.05
        )

        return max(0.0, min(10.0, round(final, 2)))

    @classmethod
    def _neighbourhood_score(cls, freguesia: Optional[str], concelho: Optional[str]) -> float:
        """Score from neighbourhood desirability lookup."""
        if not freguesia and not concelho:
            return 5.0

        freg = (freguesia or "").lower().strip()
        conc = (concelho or "").lower().strip()

        # Try Porto parishes first
        if freg in cls.PORTO_FREGUESIA_SCORES:
            return cls.PORTO_FREGUESIA_SCORES[freg]

        # Try Matosinhos parishes
        if freg in cls.MATOSINHOS_FREGUESIAS:
            return cls.MATOSINHOS_FREGUESIAS[freg]

        # Try Gaia parishes
        if freg in cls.GAIA_FREGUESIAS:
            return cls.GAIA_FREGUESIAS[freg]

        # Partial match in all parish dicts
        for lookup in [cls.PORTO_FREGUESIA_SCORES, cls.MATOSINHOS_FREGUESIAS, cls.GAIA_FREGUESIAS]:
            for key, score in lookup.items():
                if freg and (freg in key or key in freg):
                    return score

        # Fall back to concelho
        if conc in cls.CONCELHO_SCORES:
            return cls.CONCELHO_SCORES[conc]
        for key, score in cls.CONCELHO_SCORES.items():
            if conc and (conc in key or key in conc):
                return score

        return 5.0  # Unknown location

    @staticmethod
    def _metro_score(dist_metro: Optional[float]) -> float:
        """Score based on distance to nearest metro station."""
        if dist_metro is None:
            return 5.0  # Unknown

        if dist_metro < 300:
            return 10.0     # At the doorstep
        elif dist_metro < 500:
            return 9.0
        elif dist_metro < 800:
            return 7.5
        elif dist_metro < 1200:
            return 6.0
        elif dist_metro < 2000:
            return 4.0
        elif dist_metro < 3000:
            return 2.5
        else:
            return 1.0      # Very far from metro

    @staticmethod
    def _walkability_score(dist_escola: Optional[float], dist_comercio: Optional[float]) -> float:
        """Score based on proximity to schools and commerce."""
        sub_scores = []

        if dist_escola is not None:
            if dist_escola < 300:
                sub_scores.append(10.0)
            elif dist_escola < 600:
                sub_scores.append(8.0)
            elif dist_escola < 1000:
                sub_scores.append(6.0)
            elif dist_escola < 2000:
                sub_scores.append(4.0)
            else:
                sub_scores.append(2.0)

        if dist_comercio is not None:
            if dist_comercio < 200:
                sub_scores.append(10.0)
            elif dist_comercio < 500:
                sub_scores.append(8.0)
            elif dist_comercio < 1000:
                sub_scores.append(6.0)
            else:
                sub_scores.append(3.0)

        if not sub_scores:
            return 5.0

        return sum(sub_scores) / len(sub_scores)

    @staticmethod
    def _trend_score(ine_tendencia: Optional[float]) -> float:
        """Score based on market trend (monthly % change)."""
        if ine_tendencia is None:
            return 5.0

        # Strong growth = good for investment
        if ine_tendencia > 1.5:
            return 9.0
        elif ine_tendencia > 1.0:
            return 8.0
        elif ine_tendencia > 0.5:
            return 7.0
        elif ine_tendencia > 0.0:
            return 6.0
        elif ine_tendencia > -0.5:
            return 4.5
        else:
            return 3.0  # Declining market

    @staticmethod
    def _centre_proximity_score(lat: Optional[float], lon: Optional[float]) -> float:
        """Score based on distance to Porto centre (Aliados: 41.1496, -8.6109)."""
        if lat is None or lon is None:
            # Missing coordinates should reduce confidence, but not collapse the whole
            # location score. A neutral fallback preserves good neighbourhood signals.
            return 6.5

        # Haversine approximation for short distances
        PORTO_CENTER_LAT = 41.1496
        PORTO_CENTER_LON = -8.6109

        dlat = math.radians(lat - PORTO_CENTER_LAT)
        dlon = math.radians(lon - PORTO_CENTER_LON)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat)) * math.cos(math.radians(PORTO_CENTER_LAT)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c

        if distance_km < 1:
            return 10.0
        elif distance_km < 3:
            return 8.5
        elif distance_km < 5:
            return 7.0
        elif distance_km < 10:
            return 5.5
        elif distance_km < 20:
            return 4.0
        else:
            return 2.0
