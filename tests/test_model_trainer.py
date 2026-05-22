"""Tests for ModelTrainer class from Phase 4 Valuation ML Audit."""
import pytest
import numpy as np

from realestate_engine.valuation.model_trainer import ModelTrainer


def _make_listing(i: int):
    """Create a dummy listing with scrape_timestamp for time-series split."""
    return {
        "source_id": f"test-{i:03d}",
        "preco_pedido": 200000 + (i % 10) * 10000,
        "area_util_m2": 80 + (i % 7) * 10,
        "quartos": 2 + (i % 3),
        "scrape_timestamp": f"2024-01-{i+1:02d}",
    }


class TestModelTrainer:
    """Test suite for ModelTrainer class."""

    def test_initialization(self):
        """Test ModelTrainer initialization."""
        trainer = ModelTrainer()
        assert trainer is not None
        assert trainer.evaluation_results == {}
        assert trainer.test_size == 0.2
        assert trainer.random_state == 42
        assert trainer.MIN_LISTINGS == 100

    def test_split_data_basic(self):
        """Test basic train/test split with enough listings."""
        trainer = ModelTrainer()
        listings = [_make_listing(i) for i in range(120)]
        train, test = trainer.split_data(listings)
        assert len(train) == 96  # 80% of 120
        assert len(test) == 24   # 20% of 120
        assert len(train) + len(test) == 120

    def test_split_data_too_small(self):
        """Test split raises ValueError with insufficient data."""
        trainer = ModelTrainer()
        listings = [_make_listing(i) for i in range(50)]
        with pytest.raises(ValueError, match="Insufficient data"):
            trainer.split_data(listings)

    def test_split_data_time_series_order(self):
        """Test time-series split preserves chronological order."""
        trainer = ModelTrainer(time_series_split=True)
        listings = [_make_listing(i) for i in range(120)]
        train, test = trainer.split_data(listings)
        # Last train timestamp should be before first test timestamp
        assert train[-1]["scrape_timestamp"] < test[0]["scrape_timestamp"]

    def test_evaluate_metrics(self):
        """Test evaluation metrics calculation."""
        trainer = ModelTrainer()
        y_true = np.array([100, 200, 300, 400, 500])
        y_pred = np.array([110, 190, 310, 390, 510])
        metrics = trainer.evaluate(y_true, y_pred)
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] > 0
        assert metrics['rmse'] > 0
        assert -1 <= metrics['r2'] <= 1

    def test_cross_validation(self):
        """Test cross-validation functionality."""
        trainer = ModelTrainer()
        data = [_make_listing(i) for i in range(50)]

        class DummyModel:
            def train(self, train_data):
                pass
            def predict(self, listing):
                return listing.get("preco_pedido", 200000)

        model = DummyModel()
        cv_results = trainer.cross_validate(model, data, n_splits=3)
        assert 'mae_mean' in cv_results
        assert 'rmse_mean' in cv_results
        assert 'r2_mean' in cv_results

    def test_detect_overfitting_true(self):
        """Test overfitting detection when test MAE much higher than train."""
        trainer = ModelTrainer()
        assert trainer.detect_overfitting(5000, 50000, threshold=0.5) is True

    def test_detect_overfitting_false(self):
        """Test overfitting detection when test MAE similar to train."""
        trainer = ModelTrainer()
        assert trainer.detect_overfitting(5000, 6000, threshold=0.5) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
