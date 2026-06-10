"""Unit tests for normalizer."""
import pytest
from realestate_engine.etl.normalizer import Normalizer


class TestNormalizer:
    """Test normalizer functions."""
    
    def test_normalize_price_with_euro(self):
        result = Normalizer.normalize_price("350.000 €")
        assert result == 350000.0
    
    def test_normalize_price_with_comma(self):
        result = Normalizer.normalize_price("350,000")
        assert result == 350000.0
    
    def test_normalize_price_none(self):
        result = Normalizer.normalize_price(None)
        assert result is None
    
    def test_normalize_area(self):
        result = Normalizer.normalize_area("85 m²")
        assert result == 85.0
    
    def test_normalize_rooms(self):
        result = Normalizer.normalize_rooms("3 quartos")
        assert result == 3
    
    def test_normalize_tipologia(self):
        result = Normalizer.normalize_tipologia("Apartamento T3 em Lisboa")
        assert result == "T3"
    
    def test_normalize_estado_novo(self):
        result = Normalizer.normalize_estado("Apartamento novo")
        assert result == "novo"
    
    def test_normalize_full(self):
        raw = {
            "title": "T3 Novo - 350.000 €",
            "price_text": "350.000 €",
            "area_text": "120 m²",
            "rooms_text": "3 quartos",
            "condition": "Novo",
        }
        result = Normalizer.normalize(raw)
        assert result["preco_pedido"] == 350000.0
        assert result["area_util_m2"] == 120.0
        assert result["quartos"] == 3
        assert result["estado"] == "novo"
