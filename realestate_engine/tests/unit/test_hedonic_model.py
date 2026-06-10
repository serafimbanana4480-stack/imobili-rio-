"""Unit tests for HedonicModel."""
import pytest
from realestate_engine.valuation.hedonic_model import HedonicModel


class TestHedonicModel:
    """Test hedonic model functions."""

    def test_init(self):
        model = HedonicModel()
        assert model is not None

    def test_predict_with_dict(self):
        model = HedonicModel()
        listing = {
            "area_util_m2": 100.0,
            "quartos": 3,
            "casas_banho": 2,
            "freguesia": "Cedofeita",
            "concelho": "Porto",
            "estado": "novo",
            "ano_construcao": 2020,
        }
        result = model.predict(listing)
        assert isinstance(result, float)
        assert result > 0

    def test_predict_missing_data(self):
        model = HedonicModel()
        listing = {
            "area_util_m2": 100.0,
            "quartos": 3,
            "casas_banho": 2,
        }
        result = model.predict(listing)
        assert isinstance(result, float)
        assert result > 0
