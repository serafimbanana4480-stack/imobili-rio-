"""Unit tests for advanced valuation ensemble dispatch and metrics."""
from realestate_engine.valuation.advanced_ensemble import AdvancedEnsembleEngine, ModelPrediction


class TestAdvancedEnsembleDispatch:
    """Test advanced ensemble model routing and diagnostics."""

    def test_predict_single_model_routes_ine_client(self):
        engine = AdvancedEnsembleEngine()

        class INEClient:
            def estimate_value(self, listing):
                return 420000.0

        pred = engine._predict_single_model(
            INEClient(),
            {"preco_pedido": 350000.0, "area_util_m2": 120.0},
            pool=None,
        )

        assert pred.prediction == 420000.0
        assert pred.confidence == 0.7
        assert pred.explanation["source"] == "INE official statistics"

    def test_predict_single_model_routes_comps_engine(self):
        engine = AdvancedEnsembleEngine()

        class CompsEngine:
            def predict(self, listing, pool):
                return 365000.0, 0.55

        pred = engine._predict_single_model(
            CompsEngine(),
            {"preco_pedido": 350000.0, "area_util_m2": 120.0},
            pool=[{"preco_pedido": 360000.0}],
        )

        assert pred.prediction == 365000.0
        assert pred.confidence == 0.55
        assert pred.explanation["method"] == "comparative_analysis"

    def test_performance_metrics_use_statistics_variance(self):
        engine = AdvancedEnsembleEngine()
        predictions = {
            "a": ModelPrediction("a", 100.0, 0.8),
            "b": ModelPrediction("b", 120.0, 0.7),
            "c": ModelPrediction("c", 110.0, 0.9),
        }
        weights = {"a": 0.3, "b": 0.4, "c": 0.3}

        metrics = engine._calculate_performance_metrics(predictions, weights)

        assert metrics["prediction_variance"] > 0
        assert 0 <= metrics["average_confidence"] <= 1
        assert 0 <= metrics["model_agreement"] <= 1
        assert metrics["active_models"] == 3
