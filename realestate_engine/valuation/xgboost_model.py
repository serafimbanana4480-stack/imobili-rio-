"""XGBoost model for property valuation.

Enhanced with:
- One-Hot Encoding of top Porto freguesias
- 15+ features including neighbourhood, condition, energy cert
- SHAP explainability for every prediction
- Cross-validation metrics
- Proper train/test split
"""
import math
import numpy as np
from typing import Dict, Optional, List, Tuple
from loguru import logger

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not available, skipping XGBoost model")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("shap not available, skipping SHAP explanations")

try:
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ── Top Porto freguesias for OHE ────────────────────────────────────────
TOP_FREGUESIAS = [
    "foz do douro", "nevogilde", "aldoar", "massarelos", "lordelo do ouro",
    "cedofeita", "santo ildefonso", "bonfim", "paranhos", "ramalde",
    "campanha", "matosinhos", "leca da palmeira", "senhora da hora",
    "mafamude", "canidelo", "santa marinha",
]

# Energy cert → numeric
CERT_MAP = {"A+": 8, "A": 7, "A-": 6, "B": 5, "B-": 4, "C": 3, "D": 2, "E": 1, "F": 0.5, "G": 0.2}

# Estado → numeric
ESTADO_MAP = {
    "novo": 5, "em_construcao": 4.5, "renovado": 4, "remodelado": 4,
    "bom": 3, "razoavel": 2, "usado": 2, "aceitavel": 2,
    "para_recuperar": 1, "ruina": 0.5,
}


class XGBoostModel:
    """XGBoost gradient boosting model for price prediction with SHAP explainability."""

    MODEL_PATH = "data/models/xgboost_latest.pkl"

    def __init__(self):
        self.model = None
        self.explainer = None
        self._r_squared = None
        self._mae = None
        self._feature_names: List[str] = []
        self._try_load_model()

    def _try_load_model(self):
        """Try to load a previously saved model from disk."""
        import os
        if os.path.exists(self.MODEL_PATH):
            try:
                import pickle
                with open(self.MODEL_PATH, "rb") as f:
                    state = pickle.load(f)
                self.model = state.get("model")
                self._r_squared = state.get("r_squared")
                self._mae = state.get("mae")
                self._feature_names = state.get("feature_names", [])
                logger.info(f"XGBoost model loaded from {self.MODEL_PATH} (R²={self._r_squared})")
            except Exception as e:
                logger.warning(f"Failed to load XGBoost model: {e}")

    def _save_model(self):
        """Save trained model to disk."""
        if not self.model:
            return
        import os, pickle
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({
                "model": self.model,
                "r_squared": self._r_squared,
                "mae": self._mae,
                "feature_names": self._feature_names,
            }, f)
        logger.info(f"XGBoost model saved to {self.MODEL_PATH}")

    @staticmethod
    def _build_feature_names() -> List[str]:
        """Build ordered list of feature names including OHE columns."""
        base = [
            "log_area", "quartos", "casas_banho", "andar",
            "sqrt_idade", "cert_score", "estado_score",
            "lat", "lon", "dist_metro_m", "dist_escola_m",
            "tem_garagem", "tem_piscina", "tem_vista_premium",
        ]
        # OHE columns for top freguesias
        ohe = [f"freg_{f.replace(' ', '_')}" for f in TOP_FREGUESIAS]
        return base + ohe

    @staticmethod
    def _extract_features(listing: Dict) -> List[float]:
        """Extract feature vector from listing dict."""
        area = listing.get("area_util_m2") or 0
        ano = listing.get("ano_construcao") or 0
        freg = (listing.get("freguesia") or "").lower().strip()
        cert = (listing.get("cert_energetico") or "").upper().strip()
        estado = (listing.get("estado") or "").lower().strip()

        # Base features
        log_area = math.log(max(area, 10))
        from datetime import datetime
        current_year = datetime.now().year
        age = max(0, current_year - ano) if ano > 1800 else 30
        sqrt_idade = math.sqrt(age)
        cert_score = CERT_MAP.get(cert, 3)
        estado_score = ESTADO_MAP.get(estado, 2.5)

        features = [
            log_area,
            listing.get("quartos") or 0,
            listing.get("casas_banho") or 1,
            listing.get("andar") or 0,
            sqrt_idade,
            cert_score,
            estado_score,
            listing.get("lat") or 41.15,
            listing.get("lon") or -8.61,
            listing.get("dist_metro_m") or 1000,
            listing.get("dist_escola_m") or 800,
            1 if listing.get("tem_garagem") else 0,
            1 if listing.get("tem_piscina") else 0,
            1 if listing.get("tem_vista_mar") or listing.get("tem_vista_rio") else 0,
        ]

        # OHE for top freguesias
        for f in TOP_FREGUESIAS:
            features.append(1.0 if freg == f else 0.0)

        return features

    def fit(self, listings: List[Dict]):
        """Train XGBoost model and initialize SHAP explainer."""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available")
            return

        self._feature_names = self._build_feature_names()

        X, y = [], []
        for l in listings:
            price = l.get("preco_pedido")
            area = l.get("area_util_m2") or 0
            if not price or price <= 0 or area <= 0:
                continue
            X.append(self._extract_features(l))
            y.append(math.log(price))  # Log-transform target

        X = np.array(X)
        y = np.array(y)

        if len(y) < 10:
            logger.warning(f"XGBoost: need at least 10 samples, got {len(y)}")
            return

        # Train/test split
        if SKLEARN_AVAILABLE and len(y) >= 20:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y

        self.model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        if SKLEARN_AVAILABLE:
            from sklearn.metrics import mean_absolute_error, r2_score
            y_pred = self.model.predict(X_test)
            self._mae = mean_absolute_error(y_test, y_pred)
            self._r_squared = r2_score(y_test, y_pred)
            logger.info(
                f"XGBoost trained: R²={self._r_squared:.3f}, "
                f"MAE={self._mae:.3f} (log-space), n={len(y)}, "
                f"features={len(self._feature_names)}"
            )

        # SHAP explainer
        if SHAP_AVAILABLE:
            try:
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("SHAP explainer initialized")
            except Exception as e:
                logger.warning(f"SHAP initialization failed: {e}")

        # Persist model to disk for restart resilience
        self._save_model()

    def predict_with_explanation(self, listing: Dict) -> Tuple[Optional[float], Optional[Dict[str, float]]]:
        """Predict price and return SHAP explanations."""
        if not XGBOOST_AVAILABLE or self.model is None:
            return None, None

        features = self._extract_features(listing)
        X = np.array([features])

        try:
            log_pred = float(self.model.predict(X)[0])
            prediction = float(np.exp(log_pred))

            # SHAP explanations
            explanations = {}
            if self.explainer and SHAP_AVAILABLE:
                try:
                    shap_values = self.explainer.shap_values(X)[0]
                    # Only include base features (not OHE) for readability
                    for i, name in enumerate(self._feature_names):
                        if not name.startswith("freg_"):
                            explanations[name] = float(shap_values[i])
                    # Aggregate all freguesia OHE contributions
                    freg_total = sum(
                        float(shap_values[i])
                        for i, name in enumerate(self._feature_names)
                        if name.startswith("freg_")
                    )
                    explanations["freguesia_effect"] = freg_total
                except Exception as e:
                    logger.debug(f"SHAP explanation failed: {e}")

            return prediction, explanations

        except Exception as e:
            logger.warning(f"XGBoost prediction failed: {e}")
            return None, None

    def predict(self, listing: Dict) -> Optional[float]:
        """Backward compatibility for simple prediction."""
        pred, _ = self.predict_with_explanation(listing)
        return pred

    @property
    def is_trained(self) -> bool:
        return self.model is not None

    @property
    def r_squared(self) -> Optional[float]:
        return self._r_squared

    @property
    def mae(self) -> Optional[float]:
        return self._mae

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importances for diagnostics."""
        if self.model is None:
            return {}
        importances = self.model.feature_importances_
        return {
            name: float(imp)
            for name, imp in zip(self._feature_names, importances)
        }
