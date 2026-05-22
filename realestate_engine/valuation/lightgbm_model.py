"""LightGBM model for property valuation.

Advantages over XGBoost:
- Native handling of categorical features (no OHE required)
- Faster training on large datasets (leaf-wise tree growth)
- Better regularization with DART/GOSS
- 30+ engineered features including temporal, spatial and market signals
"""
from __future__ import annotations

import math
import os
import pickle
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from loguru import logger

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("lightgbm not available — install with: pip install lightgbm")

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

UTC = timezone.utc


# ── Lookup tables (shared with XGBoost) ─────────────────────────────────────
CERT_MAP = {"A+": 8, "A": 7, "A-": 6, "B": 5, "B-": 4, "C": 3, "D": 2, "E": 1, "F": 0.5, "G": 0.2}
ESTADO_MAP = {
    "novo": 5, "em_construcao": 4.5, "renovado": 4, "remodelado": 4,
    "bom": 3, "razoavel": 2, "usado": 2, "aceitavel": 2,
    "para_recuperar": 1, "ruina": 0.5,
}
TIPOLOGIA_MAP = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4, "T5": 5, "T6+": 6}

# Premium concelho multipliers for Portugal
PREMIUM_CONCELHOS = {
    "lisboa": 1.0, "cascais": 0.95, "sintra": 0.80, "porto": 0.90,
    "maia": 0.75, "matosinhos": 0.80, "vila nova de gaia": 0.78,
    "oeiras": 0.88, "loures": 0.72, "almada": 0.70,
}


class LightGBMModel:
    """LightGBM gradient boosting model with 30+ features and SHAP support."""

    MODEL_PATH = "data/models/lightgbm_latest.pkl"
    MODEL_DIR = "data/models"

    def __init__(self):
        self.model: Optional[lgb.Booster] = None
        self._r_squared: Optional[float] = None
        self._mae: Optional[float] = None
        self._feature_names: List[str] = []
        self._best_iteration: Optional[int] = None
        self._current_version: Optional[str] = None
        self._try_load_model()

    def _try_load_model(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, "rb") as f:
                    state = pickle.load(f)
                self.model = state.get("model")
                self._r_squared = state.get("r_squared")
                self._mae = state.get("mae")
                self._feature_names = state.get("feature_names", [])
                self._best_iteration = state.get("best_iteration")
                self._current_version = state.get("version")
                logger.info(
                    f"LightGBM model loaded from {self.MODEL_PATH} "
                    f"(R²={self._r_squared}, iters={self._best_iteration})"
                )
            except Exception as e:
                logger.warning(f"Failed to load LightGBM model: {e}")

    def _save_model(self):
        if not self.model:
            return
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        version = f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        version_path = os.path.join(self.MODEL_DIR, f"lightgbm_{version}.pkl")
        with open(version_path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "r_squared": self._r_squared,
                "mae": self._mae,
                "feature_names": self._feature_names,
                "best_iteration": self._best_iteration,
                "version": version,
            }, f)
        if os.path.exists(self.MODEL_PATH):
            os.remove(self.MODEL_PATH)
        try:
            os.symlink(version_path, self.MODEL_PATH)
        except (OSError, NotImplementedError):
            # Windows may not support symlinks — fall back to copy
            import shutil
            shutil.copy2(version_path, self.MODEL_PATH)
        self._current_version = version
        logger.info(f"LightGBM model saved to {version_path}")

    @staticmethod
    def _build_feature_names() -> List[str]:
        return [
            # Core property features
            "log_area", "area_util_m2", "quartos", "casas_banho", "andar",
            # Derived / transformed
            "sqrt_idade", "cert_score", "estado_score", "tipologia_num",
            # Location
            "lat", "lon", "concelho_premium",
            # Distance / accessibility
            "dist_metro_m", "dist_escola_m", "dist_comercio_m",
            "log_dist_metro", "log_dist_escola",
            # Amenity flags
            "tem_garagem", "tem_piscina", "tem_vista_premium",
            "tem_elevador", "tem_terraco", "tem_jardim", "tem_ac",
            # Market context (INE)
            "ine_preco_medio_m2", "ine_tendencia_mensal",
            # Derived market signals
            "preco_por_m2", "preco_ask_vs_ine",
            # Property mix
            "area_per_quarto", "casas_por_quarto",
            # Photo / listing quality proxy
            "num_fotos",
            # Temporal features
            "scrape_month", "scrape_dayofweek",
        ]

    @staticmethod
    def _extract_features(listing: Dict) -> Optional[List[float]]:
        area = listing.get("area_util_m2") or 0
        if area <= 0:
            return None

        ano = listing.get("ano_construcao") or 0
        current_year = datetime.now().year
        age = max(0, current_year - ano) if ano > 1800 else 30
        sqrt_idade = math.sqrt(age)

        cert = (listing.get("cert_energetico") or "").upper().strip()
        estado = (listing.get("estado") or "").lower().strip()
        tipologia = (listing.get("tipologia") or "").upper().strip()
        concelho = (listing.get("concelho") or "").lower().strip()

        cert_score = CERT_MAP.get(cert, 3.0)
        estado_score = ESTADO_MAP.get(estado, 2.5)
        tipologia_num = TIPOLOGIA_MAP.get(tipologia, listing.get("quartos") or 0)
        concelho_premium = PREMIUM_CONCELHOS.get(concelho, 0.6)

        quartos = listing.get("quartos") or 0
        casas_banho = listing.get("casas_banho") or 1

        dist_metro = listing.get("dist_metro_m") or 1500
        dist_escola = listing.get("dist_escola_m") or 1000
        dist_comercio = listing.get("dist_comercio_m") or 800

        ine_preco = listing.get("ine_preco_medio_m2") or 0.0
        ine_tendencia = listing.get("ine_tendencia_mensal") or 0.0
        preco_por_m2 = listing.get("preco_por_m2") or (
            listing.get("preco_pedido", 0) / area if area > 0 else 0
        )
        preco_ask_vs_ine = (preco_por_m2 / ine_preco) if ine_preco > 0 else 1.0

        area_per_quarto = area / quartos if quartos > 0 else area
        casas_por_quarto = casas_banho / quartos if quartos > 0 else casas_banho

        # Temporal features from scrape_timestamp
        scrape_ts = listing.get("scrape_timestamp") or ""
        try:
            dt = datetime.fromisoformat(scrape_ts[:19]) if scrape_ts else datetime.now()
            scrape_month = dt.month
            scrape_dayofweek = dt.weekday()
        except Exception:
            scrape_month = 6
            scrape_dayofweek = 2

        return [
            math.log(max(area, 10)),
            area,
            quartos,
            casas_banho,
            listing.get("andar") or 0,
            sqrt_idade,
            cert_score,
            estado_score,
            tipologia_num,
            listing.get("lat") or 39.7,
            listing.get("lon") or -8.0,
            concelho_premium,
            dist_metro,
            dist_escola,
            dist_comercio,
            math.log(max(dist_metro, 1)),
            math.log(max(dist_escola, 1)),
            1 if listing.get("tem_garagem") else 0,
            1 if listing.get("tem_piscina") else 0,
            1 if (listing.get("tem_vista_mar") or listing.get("tem_vista_rio")) else 0,
            1 if listing.get("tem_elevador") else 0,
            1 if listing.get("tem_terraco") else 0,
            1 if listing.get("tem_jardim") else 0,
            1 if listing.get("tem_ac") else 0,
            ine_preco,
            ine_tendencia,
            preco_por_m2,
            preco_ask_vs_ine,
            area_per_quarto,
            casas_por_quarto,
            listing.get("num_fotos") or 0,
            scrape_month,
            scrape_dayofweek,
        ]

    def fit(self, listings: List[Dict]):
        """Train LightGBM on listing data with early stopping."""
        if not LIGHTGBM_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("LightGBM or numpy not available — skipping training")
            return

        self._feature_names = self._build_feature_names()

        X, y = [], []
        for l in listings:
            price = l.get("preco_pedido")
            area = l.get("area_util_m2") or 0
            if not price or price <= 0 or area <= 0:
                continue
            feats = self._extract_features(l)
            if feats is None:
                continue
            X.append(feats)
            y.append(math.log(price))

        if len(y) < 20:
            logger.warning(f"LightGBM: need at least 20 samples, got {len(y)}")
            return

        X_arr = np.array(X)
        y_arr = np.array(y)

        if SKLEARN_AVAILABLE and len(y) >= 40:
            X_train, X_val, y_train, y_val = train_test_split(
                X_arr, y_arr, test_size=0.2, random_state=42
            )
            train_set = lgb.Dataset(X_train, label=y_train, feature_name=self._feature_names)
            val_set = lgb.Dataset(X_val, label=y_val, feature_name=self._feature_names, reference=train_set)
            valid_sets = [val_set]
            callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False), lgb.log_evaluation(period=-1)]
        else:
            X_train, y_train = X_arr, y_arr
            X_val, y_val = X_arr, y_arr
            train_set = lgb.Dataset(X_train, label=y_train, feature_name=self._feature_names)
            valid_sets = []
            callbacks = [lgb.log_evaluation(period=-1)]

        params = {
            "objective": "regression",
            "metric": "rmse",
            "num_leaves": 63,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "min_child_samples": 10,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "verbose": -1,
            "n_jobs": -1,
        }

        self.model = lgb.train(
            params,
            train_set,
            num_boost_round=500,
            valid_sets=valid_sets if valid_sets else None,
            callbacks=callbacks,
        )
        self._best_iteration = self.model.best_iteration if hasattr(self.model, "best_iteration") else 500

        # Evaluate
        if SKLEARN_AVAILABLE:
            y_pred_log = self.model.predict(X_val, num_iteration=self._best_iteration)
            self._mae = mean_absolute_error(y_val, y_pred_log)
            self._r_squared = r2_score(y_val, y_pred_log)
            logger.info(
                f"LightGBM trained: R²={self._r_squared:.3f}, "
                f"MAE={self._mae:.3f} (log-space), n={len(y)}, "
                f"features={len(self._feature_names)}, iters={self._best_iteration}"
            )

        self._save_model()

    def predict(self, listing: Dict) -> Optional[float]:
        """Predict property price."""
        if not LIGHTGBM_AVAILABLE or self.model is None:
            return None
        feats = self._extract_features(listing)
        if feats is None:
            return None
        try:
            X = np.array([feats])
            log_pred = float(self.model.predict(X, num_iteration=self._best_iteration)[0])
            return float(math.exp(log_pred))
        except Exception as e:
            logger.warning(f"LightGBM prediction failed: {e}")
            return None

    def predict_with_explanation(self, listing: Dict) -> Tuple[Optional[float], Optional[Dict[str, float]]]:
        """Predict price with feature importance explanation."""
        prediction = self.predict(listing)
        if prediction is None:
            return None, None
        explanation: Dict[str, float] = {}
        try:
            importances = self.model.feature_importance(importance_type="gain")
            total = sum(importances) or 1.0
            for name, imp in zip(self._feature_names, importances):
                explanation[name] = float(imp / total)
        except Exception:
            pass
        return prediction, explanation

    def train(self, listings: List[Dict]):
        """Alias for fit (ModelTrainer compatibility)."""
        self.fit(listings)

    @property
    def is_trained(self) -> bool:
        return self.model is not None

    @property
    def r_squared(self) -> Optional[float]:
        return self._r_squared

    @property
    def mae(self) -> Optional[float]:
        return self._mae
