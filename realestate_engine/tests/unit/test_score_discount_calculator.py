"""Unit tests for ScoreDiscountCalculator."""
import pytest
from realestate_engine.scoring.score_discount_calculator import ScoreDiscountCalculator


class TestScoreDiscountCalculator:
    """Test discount score calculator."""

    def test_none_discount(self):
        score = ScoreDiscountCalculator.calculate(None)
        assert score == 5.0

    def test_overpriced_20_percent(self):
        score = ScoreDiscountCalculator.calculate(-0.20)
        assert score == 0.0

    def test_overpriced_10_percent(self):
        score = ScoreDiscountCalculator.calculate(-0.10)
        assert score == 1.5

    def test_at_market_value(self):
        score = ScoreDiscountCalculator.calculate(0.0)
        assert score == 3.0

    def test_5_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.05)
        assert score == 4.5

    def test_10_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.10)
        assert score == 6.0

    def test_15_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.15)
        assert score == 7.5

    def test_20_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.20)
        assert score == 8.5

    def test_25_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.25)
        assert score == 9.3

    def test_30_percent_discount(self):
        score = ScoreDiscountCalculator.calculate(0.30)
        assert score == 10.0

    def test_deep_discount(self):
        score = ScoreDiscountCalculator.calculate(0.50)
        assert score == 10.0

    def test_extreme_overprice(self):
        score = ScoreDiscountCalculator.calculate(-0.50)
        assert score == 0.0

    def test_low_confidence(self):
        score = ScoreDiscountCalculator.calculate(0.20, confidence=0.3)
        # Should be dampened: 8.5 * 0.7 + 5.0 * 0.3 = 7.45
        assert score < 8.5
        assert score > 5.0

    def test_high_confidence(self):
        score = ScoreDiscountCalculator.calculate(0.20, confidence=0.8)
        assert score == 8.5

    def test_score_range(self):
        for discount in [-0.5, -0.2, -0.1, 0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5]:
            score = ScoreDiscountCalculator.calculate(discount)
            assert 0.0 <= score <= 10.0

    def test_returns_float(self):
        score = ScoreDiscountCalculator.calculate(0.10)
        assert isinstance(score, float)
