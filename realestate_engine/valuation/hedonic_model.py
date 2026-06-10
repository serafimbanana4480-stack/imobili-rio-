"""Hedonic pricing model using statsmodels OLS.

Expanded from 4 features to 15+ features based on Portuguese real estate
literature (Brás & Rodrigues 2020, INE Methodology 2023).
Uses Log-Linear transformation for price-area relationship and
HuberRegressor for robustness against outliers.
"""
import math
import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
from loguru import logger

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, using fallback hedonic model")

try:
    from sklearn.linear_model import HuberRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ── Porto neighbourhood median prices (INE 2025/Q4, €/m²) ──────────────
# Used ONLY as intelligent fallback when the model is not trained yet.
# Reduced by 20% to account for model overvaluation issues
PORTO_MEDIAN_PRICES_M2 = {
    # Concelho Porto - freguesias
    "foz do douro": 3360, "nevogilde": 3600, "aldoar": 2880,
    "massarelos": 3040, "lordelo do ouro": 2800, "cedofeita": 2480,
    "santo ildefonso": 2440, "se": 2320, "miragaia": 2400,
    "sao nicolau": 2360, "vitoria": 2480, "bonfim": 2200,
    "paranhos": 2080, "ramalde": 2120, "campanha": 1680,
    # Grande Porto
    "matosinhos": 2320, "leca da palmeira": 2480, "senhora da hora": 2000,
    "vila nova de gaia": 1760, "maia": 1520, "gondomar": 1200,
    "valongo": 1040, "espinho": 1760, "povoa de varzim": 1600,
    "vila do conde": 1440,
    # Defaults
    "_porto_default": 2240,
    "_grande_porto_default": 1760,
    "_portugal_default": 1440,
}

# ── Energy certificate numeric mapping ──────────────────────────────────
CERT_ENERGY_SCORES = {
    "A+": 8, "A": 7, "A-": 6, "B": 5, "B-": 4,
    "C": 3, "D": 2, "E": 1, "F": 0.5, "G": 0.2,
}

# ── Estado numeric mapping ─────────────────────────────────────────────
ESTADO_SCORES = {
    "novo": 5, "em_construcao": 4.5, "renovado": 4, "remodelado": 4,
    "bom": 3, "razoavel": 2, "usado": 2, "aceitavel": 2,
    "para_recuperar": 1, "ruina": 0.5,
}


class HedonicModel:
    """Hedonic regression model for property valuation.

    Features used (15):
      Physical:  log_area, quartos, casas_banho, andar
      Age:       idade_efectiva (2026 - ano_construcao), sqrt transform
      Quality:   cert_energetico_score, estado_score
      Location:  freguesia_median_m2, dist_metro_m, dist_escola_m, lat, lon
      Amenities: tem_garagem, tem_piscina, tem_vista_premium
    """

    FEATURES = [
        "log_area", "quartos", "casas_banho", "andar",
        "sqrt_idade", "cert_score", "estado_score",
        "freg_median_m2", "dist_metro_m", "dist_escola_m",
        "lat", "lon",
        "tem_garagem", "tem_piscina", "tem_vista_premium",
        "tem_ac", "tem_elevador", "tem_terraco", "cozinha_separada", "tem_aquecimento",
    ]

    def __init__(self):
        self.model = None
        self.huber_model = None
        self.scaler = None
        self._r_squared = None
        self._mae = None
        self._feature_names = self.FEATURES

    # ── Feature engineering ─────────────────────────────────────────────
    @staticmethod
    def _prepare_row(listing: Dict) -> Dict:
        """Transform raw listing dict into engineered features."""
        area = listing.get("area_util_m2") or 0
        ano = listing.get("ano_construcao") or 0
        freg = (listing.get("freguesia") or "").lower().strip()
        cert = (listing.get("cert_energetico") or "").upper().strip()
        estado = (listing.get("estado") or "").lower().strip()

        # Log-area (clamp to avoid log(0))
        log_area = math.log(max(area, 10))

        # Effective age (sqrt to model non-linear depreciation)
        from datetime import datetime
        current_year = datetime.now().year
        age = max(0, current_year - ano) if ano > 1800 else 30  # default 30 years
        sqrt_idade = math.sqrt(age)

        # Energy certificate numeric
        cert_score = CERT_ENERGY_SCORES.get(cert, 3)  # C as neutral default

        # Conservation state
        estado_score = ESTADO_SCORES.get(estado, 2.5)

        # Neighbourhood median price
        freg_median = PORTO_MEDIAN_PRICES_M2.get(
            freg,
            PORTO_MEDIAN_PRICES_M2.get("_porto_default", 2800)
        )

        return {
            "log_area": log_area,
            "quartos": listing.get("quartos") or 0,
            "casas_banho": listing.get("casas_banho") or 1,
            "andar": listing.get("andar") or 0,
            "sqrt_idade": sqrt_idade,
            "cert_score": cert_score,
            "estado_score": estado_score,
            "freg_median_m2": freg_median,
            "dist_metro_m": listing.get("dist_metro_m") or 1000,
            "dist_escola_m": listing.get("dist_escola_m") or 800,
            "lat": listing.get("lat") or 41.15,      # Porto centre fallback
            "lon": listing.get("lon") or -8.61,
            "tem_garagem": 1 if listing.get("tem_garagem") else 0,
            "tem_piscina": 1 if listing.get("tem_piscina") else 0,
            "tem_vista_premium": 1 if listing.get("tem_vista_mar") or listing.get("tem_vista_rio") else 0,
            # NEW: Additional amenities for Hedonic Model
            "tem_ac": 1 if listing.get("tem_ac") else 0,
            "tem_elevador": 1 if listing.get("tem_elevador") else 0,
            "tem_terraco": 1 if listing.get("tem_terraco") else 0,
            "cozinha_separada": 1 if listing.get("cozinha_separada") else 0,
            "tem_aquecimento": 1 if listing.get("tem_aquecimento") else 0,
        }

    def _build_dataframe(self, listings: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Build feature matrix X and target y from listing dicts."""
        rows = []
        prices = []
        for l in listings:
            price = l.get("preco_pedido")
            area = l.get("area_util_m2") or 0
            if not price or price <= 0 or area <= 0:
                continue
            row = self._prepare_row(l)
            rows.append(row)
            prices.append(math.log(price))  # Log-transform target

        X = pd.DataFrame(rows, columns=self.FEATURES)
        y = pd.Series(prices, name="log_price")
        return X, y

    # ── Training ────────────────────────────────────────────────────────
    def fit(self, listings: List[Dict]):
        """Train hedonic model on listing data."""
        X, y = self._build_dataframe(listings)

        if len(y) < 10:
            logger.warning(f"Hedonic model: need at least 10 samples, got {len(y)}")
            return

        # 1) statsmodels OLS for interpretability + p-values
        if STATSMODELS_AVAILABLE:
            try:
                X_sm = sm.add_constant(X)
                self.model = sm.OLS(y, X_sm).fit()
                self._r_squared = self.model.rsquared
                logger.info(
                    f"Hedonic OLS trained: R²={self._r_squared:.3f}, "
                    f"n={len(y)}, features={len(self.FEATURES)}"
                )
            except Exception as e:
                logger.warning(f"Hedonic OLS failed: {e}")

        # 2) HuberRegressor for production (robust to outliers)
        if SKLEARN_AVAILABLE:
            try:
                self.scaler = StandardScaler()
                X_scaled = self.scaler.fit_transform(X)
                self.huber_model = HuberRegressor(epsilon=1.35, max_iter=500)
                self.huber_model.fit(X_scaled, y)

                # Cross-validation MAE
                cv_scores = cross_val_score(
                    self.huber_model, X_scaled, y,
                    cv=min(5, len(y)), scoring="neg_mean_absolute_error"
                )
                self._mae = -cv_scores.mean()
                logger.info(f"Hedonic Huber trained: CV-MAE={self._mae:.3f} (log-space)")
            except Exception as e:
                logger.warning(f"Hedonic Huber failed: {e}")

    # ── Prediction ──────────────────────────────────────────────────────
    def predict(self, listing: Dict) -> Optional[float]:
        """Predict fair value for a listing."""
        area = listing.get("area_util_m2") or 0
        if area <= 0:
            return None

        # Try trained model first
        if self.huber_model is not None and self.scaler is not None:
            try:
                row = self._prepare_row(listing)
                X = pd.DataFrame([row], columns=self.FEATURES)
                X_scaled = self.scaler.transform(X)
                log_pred = self.huber_model.predict(X_scaled)[0]
                return float(np.exp(log_pred))
            except Exception as e:
                logger.warning(f"Hedonic Huber prediction failed: {e}")

        if STATSMODELS_AVAILABLE and self.model is not None:
            try:
                row = self._prepare_row(listing)
                X = pd.DataFrame([row], columns=self.FEATURES)
                X_sm = sm.add_constant(X, has_constant="add")
                log_pred = self.model.predict(X_sm).iloc[0]
                return float(np.exp(log_pred))
            except Exception as e:
                logger.warning(f"Hedonic OLS prediction failed: {e}")

        # ── Intelligent fallback (no hardcoded 3000€) ───────────────────
        return self._fallback_predict(listing)

    def _fallback_predict(self, listing: Dict) -> Optional[float]:
        """Neighbourhood-based fallback when no model is trained.

        Uses real Porto median prices per m² instead of hardcoded values.
        Applies adjustments for rooms, condition, and energy certificate.
        """
        area = listing.get("area_util_m2") or 0
        if area <= 0:
            return None

        freg = (listing.get("freguesia") or "").lower().strip()
        conc = (listing.get("concelho") or "").lower().strip()

        # Lookup median price/m²
        base_m2 = PORTO_MEDIAN_PRICES_M2.get(freg)
        if not base_m2:
            if "porto" in conc:
                base_m2 = PORTO_MEDIAN_PRICES_M2["_porto_default"]
            elif conc in PORTO_MEDIAN_PRICES_M2:
                base_m2 = PORTO_MEDIAN_PRICES_M2[conc]
            else:
                base_m2 = PORTO_MEDIAN_PRICES_M2["_grande_porto_default"]

        # Adjustments (multiplicative)
        multiplier = 1.0

        # Condition
        estado = (listing.get("estado") or "").lower()
        if estado in ("novo", "em_construcao"):
            multiplier *= 1.15
        elif estado in ("renovado", "remodelado"):
            multiplier *= 1.08
        elif estado in ("para_recuperar", "ruina"):
            multiplier *= 0.70

        # Energy certificate
        cert = (listing.get("cert_energetico") or "").upper().strip()
        if cert in ("A+", "A"):
            multiplier *= 1.06
        elif cert in ("F", "G"):
            multiplier *= 0.92

        # Garage
        if listing.get("tem_garagem"):
            multiplier *= 1.05

        # Additional amenities (ghost features now active)
        if listing.get("tem_ac"):
            multiplier *= 1.02
        if listing.get("tem_elevador"):
            multiplier *= 1.03
        if listing.get("tem_terraco"):
            multiplier *= 1.02
        if listing.get("cozinha_separada"):
            multiplier *= 1.01
        if listing.get("tem_aquecimento"):
            multiplier *= 1.02

        estimated = area * base_m2 * multiplier
        logger.debug(f"Hedonic fallback: {area}m² × {base_m2}€/m² × {multiplier:.2f} = {estimated:,.0f}€")
        return estimated

    # ── Diagnostics ─────────────────────────────────────────────────────
    @property
    def r_squared(self) -> Optional[float]:
        return self._r_squared

    @property
    def mae(self) -> Optional[float]:
        return self._mae

    @property
    def is_trained(self) -> bool:
        return self.huber_model is not None or self.model is not None

    def get_residual_std(self) -> float:
        """Return standard deviation of residuals for CI calculation."""
        if self.model is not None:
            return float(np.sqrt(self.model.mse_resid))
        return 0.15  # ~15% in log-space
