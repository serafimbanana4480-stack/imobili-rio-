"""Unit tests for ScoreLiquidityCalculator."""
import pytest
from realestate_engine.scoring.score_liquidity_calculator import ScoreLiquidityCalculator


class TestScoreLiquidityCalculator:
    """Test liquidity score calculator."""

    def test_calculate_high_liquidity(self):
        calc = ScoreLiquidityCalculator()
        score = calc.calculate(
            preco_por_m2=2000.0,
            ine_preco_medio_m2=3000.0,
            area_util_m2=70.0,
            tipologia="T2",
            quartos=2,
        )
        assert 0 <= score <= 10
        assert score > 5  # Below market price should have high liquidity

    def test_calculate_low_liquidity(self):
        calc = ScoreLiquidityCalculator()
        score = calc.calculate(
            preco_por_m2=5000.0,
            ine_preco_medio_m2=3000.0,
            area_util_m2=200.0,
            tipologia="T6",
            quartos=6,
        )
        assert 0 <= score <= 10
        assert score < 5  # Above market price and large size should have lower liquidity

    def test_calculate_missing_data(self):
        calc = ScoreLiquidityCalculator()
        score = calc.calculate(
            preco_por_m2=None,
            ine_preco_medio_m2=None,
            area_util_m2=None,
            tipologia=None,
            quartos=None,
        )
        assert 0 <= score <= 10

    def test_calculate_t3_good_area(self):
        calc = ScoreLiquidityCalculator()
        score = calc.calculate(
            preco_por_m2=2800.0,
            ine_preco_medio_m2=3000.0,
            area_util_m2=100.0,
            tipologia="T3",
            quartos=3,
        )
        assert 0 <= score <= 10

    def test_calculate_studio(self):
        calc = ScoreLiquidityCalculator()
        score = calc.calculate(
            preco_por_m2=2500.0,
            ine_preco_medio_m2=3000.0,
            area_util_m2=35.0,
            tipologia="T0",
            quartos=1,
        )
        assert 0 <= score <= 10
