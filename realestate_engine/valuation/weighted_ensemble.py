"""Weighted ensemble combining multiple valuation models.

Enhanced with:
- Dynamic confidence-based weights (models that agree more get higher weight)
- Outlier detection (reject valuations that diverge >50% from median)
- Detailed diagnostics for rationale generation
"""
import statistics
from typing import Dict, Optional, List
from loguru import logger


class WeightedEnsemble:
    """Combines hedonic, comps, INE, and XGBoost valuations with dynamic weights."""

    # Base weights — used when all models have equal confidence
    # Reduced Comps weight due to finding expensive outliers in comparables
    # Increased Hedonic/XGBoost weight but with conservative discount applied in valuation_engine
    BASE_WEIGHTS = {
        "hedonic": 0.40,
        "comps": 0.30,
        "ine": 0.05,
        "xgboost": 0.25,
    }

    # Performance tracking for adaptive weighting (auto-improvement)
    MAX_HISTORY = 50

    def __init__(self):
        self._last_weights_used = {}
        self._last_diagnostics = {}
        # model_name -> list of (prediction, actual) tuples
        self._performance_history: Dict[str, List[tuple]] = {}

    def combine(self, valuations: Dict[str, Optional[float]]) -> Optional[float]:
        """Combine valuations using confidence-weighted average with outlier rejection."""
        valid = {k: v for k, v in valuations.items() if v is not None and v > 0}

        if not valid:
            logger.warning("No valid valuations to combine")
            return None

        # If only 1 model produced a result, use it directly
        if len(valid) == 1:
            model, value = next(iter(valid.items()))
            self._last_weights_used = {model: 1.0}
            return value

        # Calculate median for outlier detection
        values_list = list(valid.values())
        median_val = statistics.median(values_list)

        # Reject outliers (>50% deviation from median)
        filtered = {}
        rejected = {}
        for model, value in valid.items():
            deviation = abs(value - median_val) / median_val
            if deviation > 0.50:
                rejected[model] = value
                logger.debug(f"Ensemble: rejecting {model}={value:,.0f} (deviation={deviation:.1%} from median={median_val:,.0f})")
            else:
                filtered[model] = value

        if not filtered:
            # If all rejected (shouldn't happen), fall back to all
            filtered = valid

        # Calculate dynamic weights based on agreement
        weights = self._calculate_dynamic_weights(filtered, median_val)
        self._last_weights_used = weights

        # Weighted average
        weighted_sum = sum(filtered[k] * weights[k] for k in filtered)
        total_weight = sum(weights[k] for k in filtered)

        if total_weight <= 0:
            return median_val

        final_value = weighted_sum / total_weight

        # Store diagnostics
        self._last_diagnostics = {
            "valid_models": list(valid.keys()),
            "rejected_models": list(rejected.keys()),
            "weights_used": weights,
            "spread_pct": self._spread_pct(filtered),
            "final_value": final_value,
            "median_value": median_val,
        }

        logger.debug(
            f"Ensemble: {', '.join(f'{k}={v:,.0f}' for k, v in filtered.items())} "
            f"→ {final_value:,.0f}€ (weights: {', '.join(f'{k}={w:.2f}' for k, w in weights.items())})"
        )
        return final_value

    def _calculate_dynamic_weights(self, valuations: Dict[str, float], median: float) -> Dict[str, float]:
        """Calculate weights dynamically based on model agreement.

        Models closer to the consensus (median) get higher weights.
        This prevents a single wildly-off model from skewing the result.
        """
        if not valuations:
            return {}

        weights = {}
        for model, value in valuations.items():
            base_w = self.BASE_WEIGHTS.get(model, 0.15)

            # Closeness to median (0-1, where 1 = exactly at median)
            if median > 0:
                deviation = abs(value - median) / median
                closeness = max(0.1, 1.0 - deviation * 2)
            else:
                closeness = 1.0

            # Performance-based adaptive boost (auto-improvement)
            boost = self._performance_boost(model)

            weights[model] = base_w * closeness * boost

        # Normalize weights to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    @staticmethod
    def _spread_pct(valuations: Dict[str, float]) -> float:
        """Calculate the spread (coefficient of variation) of valuations."""
        values = list(valuations.values())
        if len(values) < 2:
            return 0.0
        mean = statistics.mean(values)
        if mean == 0:
            return 0.0
        std = statistics.stdev(values)
        return std / mean

    def calculate_discount(self, asking_price: float, fair_value: Optional[float]) -> Optional[float]:
        """Calculate discount percentage (positive = bargain, negative = overpriced)."""
        if not fair_value or fair_value <= 0 or asking_price <= 0:
            return None
        discount = (fair_value - asking_price) / fair_value
        return round(discount, 4)

    def calculate_confidence(self, valuations: Dict[str, Optional[float]]) -> float:
        """Calculate confidence based on model agreement and count.

        Higher confidence when:
        - More models agree (low spread)
        - More models produced results
        - Models are clustered around the same value
        """
        valid = [v for v in valuations.values() if v is not None and v > 0]

        if len(valid) == 0:
            return 0.0
        if len(valid) == 1:
            return 0.40  # Single model = low confidence

        mean = statistics.mean(valid)
        if mean == 0:
            return 0.3

        std = statistics.stdev(valid) if len(valid) > 1 else 0
        cv = std / mean  # Coefficient of variation

        # Base confidence from spread
        # CV=0 → confidence=1.0, CV=0.5 → confidence=0.0
        spread_confidence = max(0.0, 1.0 - cv * 2)

        # Bonus for more models
        model_count_bonus = min(0.2, (len(valid) - 1) * 0.05)

        confidence = min(1.0, spread_confidence + model_count_bonus)
        return round(confidence, 2)

    def record_actual(self, model_name: str, prediction: float, actual: float):
        """Record a prediction vs actual sale price for adaptive weight learning.

        Called when a property sells (ground truth becomes available) to
        update the model's historical accuracy and adjust future weights.
        """
        if model_name not in self._performance_history:
            self._performance_history[model_name] = []
        self._performance_history[model_name].append((prediction, actual))
        # Keep only last N records
        if len(self._performance_history[model_name]) > self.MAX_HISTORY:
            self._performance_history[model_name].pop(0)

    def _get_model_accuracy(self, model_name: str) -> float:
        """Return mean absolute percentage error (MAPE) for a model.

        Lower MAPE = higher accuracy = higher weight boost.
        """
        history = self._performance_history.get(model_name, [])
        if len(history) < 3:
            return 0.15  # default moderate accuracy ( ~15% MAPE)
        mape = sum(abs(p - a) / a for p, a in history if a > 0) / len(history)
        return mape

    def _performance_boost(self, model_name: str) -> float:
        """Calculate weight boost based on historical accuracy.

        Models with MAPE < 10% get up to +50% weight.
        Models with MAPE > 30% get down to -50% weight.
        """
        mape = self._get_model_accuracy(model_name)
        if mape < 0.10:
            return 1.5
        elif mape < 0.20:
            return 1.2
        elif mape < 0.30:
            return 1.0
        elif mape < 0.50:
            return 0.7
        else:
            return 0.5

    @property
    def last_weights(self) -> Dict[str, float]:
        return self._last_weights_used

    @property
    def last_diagnostics(self) -> Dict:
        return self._last_diagnostics

    def enable_adaptive_learning(self):
        """Enable adaptive weight learning pipeline.

        This method documents how to activate the adaptive learning feature.
        To actually feed real transaction prices back into the ensemble:

        1. Create a post-sale / post-valuation feedback pipeline (e.g., a cron job
           or API endpoint) that receives the actual transaction price.
        2. Call ``record_actual(model_name, prediction, actual)`` for each model
           that produced a valuation for the sold property.
        3. The ensemble will automatically adjust future weights based on
           historical MAPE via ``_performance_boost()``.

        Example usage in a feedback job::

            ensemble = WeightedEnsemble()
            ensemble.record_actual("xgboost", predicted=350_000, actual=320_000)
            ensemble.record_actual("hedonic", predicted=340_000, actual=320_000)

        Metrics (MAPE per model) can be exported to Prometheus/Grafana via
        ``get_performance_report()``.
        """
        logger.info("Adaptive learning enabled. Remember to call record_actual() via feedback pipeline.")

    def get_performance_report(self) -> Dict[str, Dict]:
        report = {}
        for model, history in self._performance_history.items():
            if len(history) < 1:
                continue
            mape = self._get_model_accuracy(model)
            report[model] = {
                "samples": len(history),
                "mape": round(mape, 4),
                "weight_boost": round(self._performance_boost(model), 2),
                "last_prediction": round(history[-1][0], 2),
                "last_actual": round(history[-1][1], 2),
            }
        return report
