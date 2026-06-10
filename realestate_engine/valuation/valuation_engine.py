"""Valuation engine orchestrating all valuation models.

Enhanced to:
- Pass expanded features (energy cert, state, garage, etc.) to all models
- Include model diagnostics in output
- Track ensemble weights and diagnostics
- Provide comps details for rationale
- Include INE market context
"""
import asyncio
import statistics
from typing import Dict, List, Optional
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import Valuation, CleanListing
from realestate_engine.valuation.hedonic_model import HedonicModel
from realestate_engine.valuation.xgboost_model import XGBoostModel
from realestate_engine.valuation.comps_engine import CompsEngine
from realestate_engine.valuation.ine_client import INEClient
from realestate_engine.valuation.weighted_ensemble import WeightedEnsemble
from realestate_engine.valuation.confidence_interval import ConfidenceInterval
from realestate_engine.valuation.advanced_ensemble import get_advanced_ensemble, EnsembleResult, ModelPrediction
from realestate_engine.monitoring.metrics import MetricsCollector
from realestate_engine.utils.decorators import async_timed

metrics = MetricsCollector()


def _listing_to_full_dict(listing) -> Dict:
    """Convert a CleanListing ORM object to a full feature dict."""
    return {
        "preco_pedido": listing.preco_pedido,
        "area_util_m2": listing.area_util_m2,
        "quartos": listing.quartos,
        "casas_banho": listing.casas_banho,
        "ano_construcao": listing.ano_construcao,
        "freguesia": listing.freguesia,
        "concelho": listing.concelho,
        "distrito": listing.distrito,
        "lat": listing.lat,
        "lon": listing.lon,
        "dist_metro_m": listing.dist_metro_m,
        "dist_escola_m": listing.dist_escola_m,
        "dist_comercio_m": listing.dist_comercio_m,
        # Expanded features for hedonic/xgboost
        "estado": listing.estado,
        "cert_energetico": listing.cert_energetico,
        "tipologia": listing.tipologia,
        "preco_por_m2": listing.preco_por_m2,
        "ine_preco_medio_m2": listing.ine_preco_medio_m2,
        "ine_tendencia_mensal": listing.ine_tendencia_mensal,
        "num_fotos": listing.num_fotos,
        "scrape_timestamp": listing.scrape_timestamp,
        "source_id": listing.source_id,
        "source_portal": listing.source_portal,
        # Amenity flags (may be None if not available)
        "tem_garagem": getattr(listing, "tem_garagem", None),
        "tem_piscina": getattr(listing, "tem_piscina", None),
        "tem_vista_mar": getattr(listing, "tem_vista_mar", None),
        "tem_vista_rio": getattr(listing, "tem_vista_rio", None),
        "andar": getattr(listing, "andar", None),
    }


class ValuationEngine:
    """Orchestrates property valuation pipeline."""
    
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        self.hedonic = HedonicModel()
        self.comps = CompsEngine()
        self.ine = INEClient()
        self.xgboost = XGBoostModel()
        self.ensemble = WeightedEnsemble()
        self.ci = ConfidenceInterval()
        self._models_trained = False

    def _train_models(self, listings: List[Dict]):
        """Train models on existing listings."""
        if self._models_trained or len(listings) < 10:
            if len(listings) < 10:
                logger.warning(f"Valuation: need ≥10 listings for training, got {len(listings)}")
            return

        self.hedonic.fit(listings)
        self.xgboost.fit(listings)
        self._models_trained = True

        # Log model health
        if self.hedonic.is_trained:
            logger.info(f"Hedonic R²={self.hedonic.r_squared:.3f}" if self.hedonic.r_squared else "Hedonic trained")
        if self.xgboost.is_trained:
            logger.info(f"XGBoost R²={self.xgboost.r_squared:.3f}" if self.xgboost.r_squared else "XGBoost trained")

    def retrain(self):
        """Force retraining and save models to disk."""
        logger.info("Force retraining valuation models...")
        listings = self.repo.get_clean_listings(limit=10000)
        pool = [_listing_to_full_dict(l) for l in listings]

        self._models_trained = False  # Reset to allow retrain
        self._train_models(pool)

        # Save logic (joblib for sklearn, native XGBoost format for XGBoost)
        import os
        import joblib
        from realestate_engine.utils.config import config

        model_dir = os.path.join(config.data_dir, "models")
        os.makedirs(model_dir, exist_ok=True)

        if self.xgboost.model:
            self.xgboost.model.save_model(
                os.path.join(model_dir, "xgboost_latest.json")
            )

        if self.hedonic.huber_model:
            joblib.dump({
                "model": self.hedonic.huber_model,
                "scaler": self.hedonic.scaler,
            }, os.path.join(model_dir, "hedonic_latest.joblib"))

        logger.info(f"Models saved to {model_dir}")
        return len(pool)

    def valuate_advanced(self, listing: Dict, pool: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Valuate using advanced 8-model ensemble with meta-learning."""
        if not listing.get("preco_pedido") or listing.get("preco_pedido") <= 0:
            return None

        try:
            # Get advanced ensemble prediction
            advanced_ensemble = get_advanced_ensemble()
            ensemble_result = advanced_ensemble.predict_with_meta_learning(listing, pool)
            
            # Convert to expected format
            return {
                "valor_justo": round(ensemble_result.fair_value, 2),
                "ci_lower": round(ensemble_result.confidence_interval[0], 2),
                "ci_upper": round(ensemble_result.confidence_interval[1], 2),
                "confianca": round(ensemble_result.ensemble_confidence, 2),
                "valuation_quality": self._build_valuation_quality(
                    listing,
                    ensemble_result.fair_value,
                    ensemble_result.confidence_interval,
                    ensemble_result.ensemble_confidence,
                    ensemble_result.individual_predictions,
                    pool or [],
                ),
                "value_risk": self._build_value_risk(
                    ensemble_result.ensemble_confidence,
                    ensemble_result.confidence_interval,
                    ensemble_result.individual_predictions,
                ),
                "ensemble_weights": ensemble_result.model_weights,
                "models_active": len(ensemble_result.individual_predictions),
                "ensemble_performance": ensemble_result.ensemble_performance,
                "meta_features": ensemble_result.meta_features,
                
                # Individual model predictions
                "individual_predictions": {
                    name: {
                        "value": round(pred.prediction, 2) if pred.prediction is not None else None,
                        "confidence": round(pred.confidence, 2) if pred.confidence is not None else 0,
                        "explanation": pred.explanation
                    }
                    for name, pred in ensemble_result.individual_predictions.items()
                },
                
                # Legacy compatibility
                "hedonic_value": round(ensemble_result.individual_predictions.get("hedonic", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("hedonic", ModelPrediction("", 0, 0)).prediction is not None else None,
                "comps_value": round(ensemble_result.individual_predictions.get("comps", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("comps", ModelPrediction("", 0, 0)).prediction is not None else None,
                "ine_value": round(ensemble_result.individual_predictions.get("ine", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("ine", ModelPrediction("", 0, 0)).prediction is not None else None,
                "xgboost_value": round(ensemble_result.individual_predictions.get("xgboost", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("xgboost", ModelPrediction("", 0, 0)).prediction is not None else None,
                
                # Additional advanced models
                "neural_network_value": round(ensemble_result.individual_predictions.get("neural_network", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("neural_network", ModelPrediction("", 0, 0)).prediction is not None else None,
                "catboost_value": round(ensemble_result.individual_predictions.get("catboost", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("catboost", ModelPrediction("", 0, 0)).prediction is not None else None,
                "random_forest_value": round(ensemble_result.individual_predictions.get("random_forest", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("random_forest", ModelPrediction("", 0, 0)).prediction is not None else None,
                "linear_model_value": round(ensemble_result.individual_predictions.get("linear", ModelPrediction("", 0, 0)).prediction, 2) if ensemble_result.individual_predictions.get("linear", ModelPrediction("", 0, 0)).prediction is not None else None,
                
                # Market context (from INE)
                "market_context": self.ine.get_market_context(
                    listing.get("freguesia", ""),
                    listing.get("concelho", ""),
                ),
            }
            
        except Exception as e:
            logger.error(f"Advanced valuation failed: {e}")
            # Fallback to standard valuation
            return self.valuate(listing, pool)

    def valuate(self, listing: Dict, pool: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Valuate a single listing using all 4 layers."""
        if not listing.get("preco_pedido") or listing.get("preco_pedido") <= 0:
            return None

        # Train models if needed
        if not self._models_trained and pool:
            self._train_models(pool)

        # Run individual models
        xgboost_val, xgboost_explanation = self.xgboost.predict_with_explanation(listing)
        comps_val, comps_conf = self.comps.predict(listing, pool or [])

        valuations = {
            "hedonic": self.hedonic.predict(listing),
            "comps": comps_val,
            "ine": self.ine.estimate_value(listing),
            "xgboost": xgboost_val,
        }

        # Combine with ensemble
        fair_value = self.ensemble.combine(valuations)
        if not fair_value:
            return None

        # Conservative adjustment for low-data scenarios
        # Instead of arbitrary 20% slashes, we blend with the asking price based on confidence
        # but for the "fair_value" column we should stay as honest as possible.
        
        # We'll keep a "conservative_value" for internal scoring but report the 
        # model's fair_value to the user with a confidence indicator.
        
        # For now, let's keep it honest but add a safety margin only if confidence is very low.
        ensemble_conf = self.ensemble.calculate_confidence(valuations)
        
        if ensemble_conf < 0.3:
            # Very low confidence: models disagree wildly or too few models
            # Apply a 15% safety margin to the fair value
            fair_value = fair_value * 0.85

        discount = self.ensemble.calculate_discount(listing["preco_pedido"], fair_value)

        # Blend geometric comps confidence with ensemble spread confidence
        if comps_conf > 0:
            confidence = round((ensemble_conf * 0.45) + (comps_conf * 0.55), 2)
        else:
            confidence = ensemble_conf

        # Confidence interval
        values = [v for v in valuations.values() if v]
        if values:
            ci_lower, ci_upper = self.ci.from_valuations(values)
        else:
            ci_lower, ci_upper = fair_value * 0.85, fair_value * 1.15

        # INE market context
        market_context = self.ine.get_market_context(
            listing.get("freguesia", ""),
            listing.get("concelho", ""),
        )

        valuation_quality = self._build_valuation_quality(
            listing,
            fair_value,
            (ci_lower, ci_upper),
            confidence,
            valuations,
            pool or [],
        )

        value_risk = self._build_value_risk(
            confidence,
            (ci_lower, ci_upper),
            valuations,
        )

        return {
            "valor_justo": round(fair_value, 2),
            "hedonic_value": round(valuations["hedonic"], 2) if valuations["hedonic"] else None,
            "comps_value": round(valuations["comps"], 2) if valuations["comps"] else None,
            "ine_value": round(valuations["ine"], 2) if valuations["ine"] else None,
            "xgboost_value": round(valuations["xgboost"], 2) if valuations["xgboost"] else None,
            "xgboost_explanation": xgboost_explanation,
            "ci_lower": round(ci_lower, 2),
            "ci_upper": round(ci_upper, 2),
            "discount": discount,
            "confianca": confidence,
            "valuation_quality": valuation_quality,
            "value_risk": value_risk,
            "ensemble_weights": self.ensemble.last_weights,
            "market_context": market_context,
            "models_active": sum(1 for v in valuations.values() if v is not None),
        }

    def _build_valuation_quality(
        self,
        listing: Dict,
        fair_value: float,
        ci: tuple,
        confidence: float,
        model_values: Dict,
        pool: List[Dict],
    ) -> Dict[str, object]:
        """Build a commercial-quality diagnosis for the valuation output.

        This makes the result easier to explain to a client by translating
        raw model output into business language: reliability, spread and data coverage.
        """
        ci_lower, ci_upper = ci
        ci_width_pct = 0.0
        if fair_value and fair_value > 0:
            ci_width_pct = max(0.0, (ci_upper - ci_lower) / fair_value)

        valid_models = [v.prediction for v in model_values.values() if hasattr(v, 'prediction') and v.prediction is not None and v.prediction > 0]
        model_spread_pct = 0.0
        if len(valid_models) > 1:
            mean_val = statistics.mean(valid_models)
            if mean_val > 0:
                model_spread_pct = statistics.stdev(valid_models) / mean_val

        coverage = {
            "has_location": bool(listing.get("freguesia") or listing.get("concelho")),
            "has_coords": bool(listing.get("lat") and listing.get("lon")),
            "has_price": bool(listing.get("preco_pedido") and listing.get("preco_pedido") > 0),
            "has_area": bool(listing.get("area_util_m2") and listing.get("area_util_m2") > 0),
            "has_comps_pool": bool(pool and len(pool) >= 3),
            "pool_size": len(pool),
            "active_models": len(valid_models),
        }

        if confidence >= 0.75 and ci_width_pct <= 0.20:
            band = "forte"
        elif confidence >= 0.55 and ci_width_pct <= 0.35:
            band = "moderada"
        else:
            band = "cautelosa"

        return {
            "band": band,
            "confidence": round(confidence, 2),
            "ci_width_pct": round(ci_width_pct, 4),
            "model_spread_pct": round(model_spread_pct, 4),
            "coverage": coverage,
            "summary": self._quality_summary(band, coverage, ci_width_pct, model_spread_pct),
        }

    @staticmethod
    def _build_value_risk(confidence: float, ci: tuple, model_values: Dict) -> Dict[str, object]:
        """Translate valuation uncertainty into a business-friendly risk label."""
        ci_lower, ci_upper = ci
        valid_values = [v.prediction for v in model_values.values() if hasattr(v, 'prediction') and v.prediction is not None and v.prediction > 0]

        risk_score = 0.0
        if confidence < 0.45:
            risk_score += 0.45
        elif confidence < 0.65:
            risk_score += 0.25

        if ci_upper > 0 and ci_lower > 0:
            width = (ci_upper - ci_lower) / ((ci_upper + ci_lower) / 2)
            if width > 0.40:
                risk_score += 0.35
            elif width > 0.25:
                risk_score += 0.20

        if len(valid_values) <= 1:
            risk_score += 0.20
        elif len(valid_values) <= 2:
            risk_score += 0.10

        risk_score = min(1.0, risk_score)
        if risk_score >= 0.7:
            label = "alto"
        elif risk_score >= 0.35:
            label = "médio"
        else:
            label = "baixo"

        return {
            "label": label,
            "score": round(risk_score, 2),
            "valid_models": len(valid_values),
            "message": {
                "alto": "Valor com incerteza relevante; usar como referência e não como prova final.",
                "médio": "Valor útil para decisão, mas recomenda-se validação adicional.",
                "baixo": "Valor estável e com boa base comparativa.",
            }[label],
        }

    @staticmethod
    def _quality_summary(band: str, coverage: Dict[str, object], ci_width_pct: float, model_spread_pct: float) -> str:
        """Create a short commercial summary for dashboards and APIs."""
        if band == "forte":
            return "Valuation sólido, com boa cobertura de dados e intervalo controlado."
        if band == "moderada":
            return "Valuation utilizável para decisão, mas com alguma sensibilidade à qualidade dos dados."
        return (
            "Valuation mais cauteloso devido a cobertura limitada, spread elevado ou falta de comparáveis suficientes."
        )

    @async_timed
    async def valuate_batch(self, batch_size: int = 500) -> int:
        """Valuate all unvaluated listings."""
        logger.info("Starting valuation batch")

        # Purity guard — never valuate synthetic/sample data
        self.repo.assert_no_sample_data()

        listings = self.repo.get_clean_listings(limit=batch_size)
        if not listings:
            logger.info("No listings to valuate")
            return 0

        # Convert to full feature dicts for model training
        pool = [_listing_to_full_dict(l) for l in listings]

        self._train_models(pool)

        valuations = []
        for i, listing in enumerate(listings):
            # Check if already has valuation
            existing = self.repo.get_valuation_by_listing(listing.id)
            if existing:
                continue

            result = self.valuate(_listing_to_full_dict(listing), pool)

            if result:
                valuation = Valuation(
                    listing_id=listing.id,
                    valor_justo=result["valor_justo"],
                    hedonic_value=result["hedonic_value"],
                    comps_value=result["comps_value"],
                    ine_value=result["ine_value"],
                    xgboost_value=result["xgboost_value"],
                    xgboost_explanation=result["xgboost_explanation"],
                    ci_lower=result["ci_lower"],
                    ci_upper=result["ci_upper"],
                    discount=result["discount"],
                    confianca=result["confianca"],
                )
                valuations.append(valuation)

        if valuations:
            self.repo.create_valuations_batch(valuations)
            logger.info(f"Valuated {len(valuations)} listings")

            # Log valuation stats
            discounts = [v.discount for v in valuations if v.discount is not None]
            if discounts:
                import statistics
                logger.info(
                    f"Discount stats: median={statistics.median(discounts):.1%}, "
                    f"mean={statistics.mean(discounts):.1%}, "
                    f"bargains(>10%)={sum(1 for d in discounts if d > 0.10)}"
                )

        return len(valuations)
