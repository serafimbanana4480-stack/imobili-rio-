"""Unit tests for ScoringEngine."""
import pytest
from unittest.mock import MagicMock, patch
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.models import CleanListing, Valuation


class TestScoringEngine:
    """Test scoring engine functions."""

    def test_init(self):
        engine = ScoringEngine()
        assert engine.repo is not None
        assert engine.discount_calc is not None
        assert engine.condition_calc is not None
        assert engine.liquidity_calc is not None
        assert engine.freshness_calc is not None
        assert engine.red_flags is not None
        assert engine.weighted_calc is not None
        assert engine.rationale_gen is not None

    def test_score_without_valuation(self):
        engine = ScoringEngine()
        listing = CleanListing(
            source_portal="idealista",
            source_id="1",
            source_url="https://idealista.pt/1",
            scrape_timestamp="2024-01-01",
            titulo="T3 Porto",
            preco_pedido=300000.0,
            area_util_m2=100.0,
            quartos=3,
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            estado="novo",
            tipologia="T3",
        )
        result = engine.score(listing, valuation=None)
        assert "score_total" in result
        assert "score_discount" in result
        assert "score_location" in result
        assert "score_condition" in result
        assert "score_liquidity" in result
        assert "score_freshness" in result
        assert 0 <= result["score_total"] <= 10

    def test_score_with_valuation(self):
        engine = ScoringEngine()
        listing = CleanListing(
            source_portal="idealista",
            source_id="1",
            source_url="https://idealista.pt/1",
            scrape_timestamp="2024-01-01",
            titulo="T3 Porto",
            preco_pedido=270000.0,  # Below market
            area_util_m2=100.0,
            quartos=3,
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            estado="novo",
            tipologia="T3",
            ine_preco_medio_m2=3000.0,
        )
        valuation = Valuation(
            listing_id="1",
            valor_justo=300000.0,
            discount=0.10,
            confianca=0.8,
        )
        result = engine.score(listing, valuation=valuation)
        assert result["score_total"] > 0
        assert result["score_discount"] > 3.0  # Should have good discount score

    def test_score_range_validation(self):
        engine = ScoringEngine()
        listing = CleanListing(
            source_portal="idealista",
            source_id="1",
            source_url="https://idealista.pt/1",
            scrape_timestamp="2024-01-01",
            titulo="T3 Porto",
            preco_pedido=300000.0,
            area_util_m2=100.0,
            quartos=3,
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            estado="novo",
            tipologia="T3",
        )
        result = engine.score(listing, valuation=None)
        assert 0 <= result["score_total"] <= 10
        assert 0 <= result["score_discount"] <= 10
        assert 0 <= result["score_location"] <= 10
        assert 0 <= result["score_condition"] <= 10
        assert 0 <= result["score_liquidity"] <= 10
        assert 0 <= result["score_freshness"] <= 10
