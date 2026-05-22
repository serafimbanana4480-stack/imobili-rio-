"""Location score calculator (25% weight).

National coverage location scoring with:
- All Porto, Matosinhos, Gaia freguesias with desirability scores
- Key concelhos across all 7 regions (Norte, Centro, Lisboa, Alentejo, Algarve, Madeira, Acores)
- District-level fallback scores
- Metro proximity scoring
- Walkability (schools, commerce)
- Market trend integration
- Multi-city centre proximity (Porto, Lisboa, Faro, Funchal, etc.)
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

    # ── National concelho scores (all regions) ────────────────────────
    CONCELHO_SCORES = {
        # Norte
        "porto": 8.0, "matosinhos": 7.8, "vila nova de gaia": 7.0,
        "maia": 6.0, "gondomar": 5.5, "valongo": 5.0,
        "espinho": 7.0, "vila do conde": 6.3, "povoa de varzim": 6.5,
        "santo tirso": 4.5, "trofa": 4.8, "paredes": 4.3,
        "penafiel": 4.0, "pacos de ferreira": 4.0, "lousada": 3.8,
        "felgueiras": 3.5, "amarante": 4.2, "marco de canaveses": 3.8,
        "braga": 7.2, "guimaraes": 6.5, "vila nova de famalicao": 5.8,
        "barcelos": 5.5, "esposende": 6.8,
        "viana do castelo": 6.5, "caminha": 6.8,
        "vila real": 5.5, "chaves": 5.0,
        "braganca": 5.0,
        "santa maria da feira": 5.5, "sao joao da madeira": 5.8,
        # Centro
        "coimbra": 7.0, "figueira da foz": 6.5,
        "aveiro": 7.2, "ilhavo": 6.8, "ovar": 5.8,
        "viseu": 6.2,
        "leiria": 6.0, "caldas da rainha": 6.2, "peniche": 6.5,
        "nazare": 7.0, "obidos": 6.8, "alcobaca": 5.5,
        "guarda": 4.8, "covilha": 5.0,
        "castelo branco": 5.2,
        "tomar": 5.0, "abrantes": 4.8,
        # Lisboa / AML
        "lisboa": 9.0, "cascais": 9.2, "oeiras": 8.5,
        "sintra": 7.5, "loures": 6.8, "amadora": 6.5,
        "odivelas": 6.8, "seixal": 6.5, "almada": 7.2,
        "barreiro": 5.5, "setubal": 6.5, "sesimbra": 7.5,
        "mafra": 6.5, "torres vedras": 6.0,
        # Alentejo
        "evora": 6.0, "beja": 5.0, "portalegre": 4.8,
        "sines": 6.5, "alcacer do sal": 5.2,
        "elvas": 5.0, "estremoz": 5.2, "montemor-o-novo": 5.0,
        # Algarve
        "faro": 7.5, "lou le": 7.8, "albufeira": 7.5,
        "portimao": 7.2, "lagos": 7.5, "tavira": 7.0,
        "silves": 6.5, "vila real de santo antonio": 6.8, "olhao": 6.8,
        # Madeira
        "funchal": 7.5, "santa cruz": 6.5,
        "camara de lobos": 6.2, "machico": 6.0,
        # Acores
        "ponta delgada": 6.0, "angra do heroismo": 5.8, "horta": 5.5,
    }

    # ── District-level fallback scores ─────────────────────────────────
    DISTRITO_SCORES = {
        "porto": 6.5, "braga": 6.0, "viana do castelo": 5.8,
        "vila real": 5.0, "braganca": 4.5,
        "aveiro": 6.2, "viseu": 5.5, "coimbra": 6.0,
        "leiria": 5.8, "guarda": 4.5, "castelo branco": 4.8,
        "santarem": 5.0,
        "lisboa": 8.0,
        "setubal": 6.5,
        "portalegre": 4.5, "evora": 5.5, "beja": 4.8,
        "faro": 7.0,
        "funchal": 6.8,
        "ponta delgada": 5.5, "angra do heroismo": 5.2, "horta": 5.0,
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

        # District-level fallback
        if conc in cls._CONCELHO_TO_DISTRITO:
            distrito = cls._CONCELHO_TO_DISTRITO[conc]
            if distrito in cls.DISTRITO_SCORES:
                return cls.DISTRITO_SCORES[distrito]

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

    # ── Major city centers for proximity scoring ──────────────────────
    _CITY_CENTERS = [
        (41.1496, -8.6109, "Porto"),
        (38.7223, -9.1393, "Lisboa"),
        (37.0179, -7.9308, "Faro"),
        (32.6496, -16.9086, "Funchal"),
        (37.7412, -25.6756, "Ponta Delgada"),
        (40.2033, -8.4103, "Coimbra"),
        (41.5518, -8.4229, "Braga"),
    ]

    # ── Concelho → Distrito mapping (shared with INEClient) ────────────
    _CONCELHO_TO_DISTRITO = {
        "porto": "porto", "matosinhos": "porto", "vila nova de gaia": "porto",
        "maia": "porto", "gondomar": "porto", "valongo": "porto", "espinho": "porto",
        "vila do conde": "porto", "povoa de varzim": "porto", "santo tirso": "porto",
        "trofa": "porto", "paredes": "porto", "penafiel": "porto",
        "pacos de ferreira": "porto", "lousada": "porto", "felgueiras": "porto",
        "amarante": "porto", "marco de canaveses": "porto",
        "braga": "braga", "guimaraes": "braga", "vila nova de famalicao": "braga",
        "barcelos": "braga", "esposende": "braga",
        "viana do castelo": "viana do castelo", "caminha": "viana do castelo",
        "vila real": "vila real", "chaves": "vila real",
        "braganca": "braganca",
        "santa maria da feira": "aveiro", "sao joao da madeira": "aveiro",
        "aveiro": "aveiro", "ilhavo": "aveiro", "ovar": "aveiro",
        "viseu": "viseu",
        "coimbra": "coimbra", "figueira da foz": "coimbra",
        "leiria": "leiria", "caldas da rainha": "leiria", "peniche": "leiria",
        "nazare": "leiria", "obidos": "leiria", "alcobaca": "leiria",
        "guarda": "guarda", "covilha": "guarda",
        "castelo branco": "castelo branco",
        "tomar": "santarem", "abrantes": "santarem",
        "lisboa": "lisboa", "cascais": "lisboa", "oeiras": "lisboa",
        "sintra": "lisboa", "loures": "lisboa", "amadora": "lisboa",
        "odivelas": "lisboa", "mafra": "lisboa", "torres vedras": "lisboa",
        "seixal": "setubal", "almada": "setubal", "barreiro": "setubal",
        "setubal": "setubal", "sesimbra": "setubal", "sines": "setubal",
        "alcacer do sal": "setubal",
        "evora": "evora", "estremoz": "evora", "montemor-o-novo": "evora",
        "beja": "beja",
        "portalegre": "portalegre", "elvas": "portalegre",
        "faro": "faro", "lou le": "faro", "albufeira": "faro",
        "portimao": "faro", "lagos": "faro", "tavira": "faro",
        "silves": "faro", "vila real de santo antonio": "faro", "olhao": "faro",
        "funchal": "funchal", "santa cruz": "funchal",
        "camara de lobos": "funchal", "machico": "funchal",
        "ponta delgada": "ponta delgada", "angra do heroismo": "angra do heroismo",
        "horta": "horta",
    }

    @staticmethod
    def _centre_proximity_score(lat: Optional[float], lon: Optional[float]) -> float:
        """Score based on distance to nearest major city center."""
        if lat is None or lon is None:
            return 6.5

        best_score = 2.0
        for center_lat, center_lon, _ in ScoreLocationCalculator._CITY_CENTERS:
            dlat = math.radians(lat - center_lat)
            dlon = math.radians(lon - center_lon)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(center_lat)) *
                 math.sin(dlon / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))
            distance_km = 6371 * c

            if distance_km < 1:
                score = 10.0
            elif distance_km < 3:
                score = 8.5
            elif distance_km < 5:
                score = 7.0
            elif distance_km < 10:
                score = 5.5
            elif distance_km < 20:
                score = 4.0
            else:
                score = 2.0

            if score > best_score:
                best_score = score

        return best_score
