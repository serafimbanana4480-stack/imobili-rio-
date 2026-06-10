"""Unit tests for WeightedScoreCalculator."""
import pytest
from realestate_engine.scoring.weighted_score_calculator import WeightedScoreCalculator


class TestWeightedScoreCalculator:
    """Test weighted score calculation and classification."""

    def test_calculate_all_perfect(self):
        calc = WeightedScoreCalculator()
        scores = {
            "discount": 10.0,
            "location": 10.0,
            "condition": 10.0,
            "amenities": 10.0,
            "liquidity": 10.0,
            "freshness": 10.0,
        }
        result = calc.calculate(scores)
        assert result == 10.0

    def test_calculate_all_zero(self):
        calc = WeightedScoreCalculator()
        scores = {
            "discount": 0.0,
            "location": 0.0,
            "condition": 0.0,
            "amenities": 0.0,
            "liquidity": 0.0,
            "freshness": 0.0,
        }
        result = calc.calculate(scores)
        assert result == 0.0

    def test_calculate_missing_factor_defaults_to_neutral(self):
        calc = WeightedScoreCalculator()
        scores = {"discount": 10.0}
        result = calc.calculate(scores)
        assert 0 < result < 10.0

    def test_calculate_range(self):
        calc = WeightedScoreCalculator()
        scores = {
            "discount": 7.0,
            "location": 6.0,
            "condition": 8.0,
            "amenities": 5.0,
            "liquidity": 7.0,
            "freshness": 6.0,
        }
        result = calc.calculate(scores)
        assert 0 <= result <= 10.0

    def test_classify_imperdivel(self):
        assert WeightedScoreCalculator.classify(9.5, is_imperdivel_verified=True) == "Imperdível"

    def test_classify_excelente(self):
        assert WeightedScoreCalculator.classify(8.0) == "Excelente"

    def test_classify_bom(self):
        assert WeightedScoreCalculator.classify(6.5) == "Bom"

    def test_classify_aceitavel(self):
        assert WeightedScoreCalculator.classify(5.0) == "Aceitável"

    def test_classify_abaixo_da_media(self):
        assert WeightedScoreCalculator.classify(3.5) == "Abaixo da média"

    def test_classify_nao_recomendado(self):
        assert WeightedScoreCalculator.classify(1.0) == "Não recomendado"

    def test_classify_high_score_not_imperdivel_downgrades(self):
        assert WeightedScoreCalculator.classify(9.2, is_imperdivel_verified=False) == "Excelente"

    def test_is_imperdivel_passes(self):
        assert WeightedScoreCalculator.is_imperdivel(9.5, 20.0, has_any_flags=False)

    def test_is_imperdivel_fails_low_score(self):
        assert not WeightedScoreCalculator.is_imperdivel(8.5, 20.0, has_any_flags=False)

    def test_is_imperdivel_fails_low_discount(self):
        assert not WeightedScoreCalculator.is_imperdivel(9.5, 10.0, has_any_flags=False)

    def test_is_imperdivel_fails_has_flags(self):
        assert not WeightedScoreCalculator.is_imperdivel(9.5, 20.0, has_any_flags=True)

    def test_custom_weights(self):
        custom = {"discount": 0.5, "location": 0.5}
        calc = WeightedScoreCalculator(weights=custom)
        scores = {"discount": 10.0, "location": 0.0}
        result = calc.calculate(scores)
        assert result == 5.0

    def test_weights_normalization(self):
        custom = {"discount": 2.0, "location": 2.0}
        calc = WeightedScoreCalculator(weights=custom)
        scores = {"discount": 10.0, "location": 0.0}
        result = calc.calculate(scores)
        assert result == 5.0

    def test_classify_with_emoji(self):
        label, emoji = WeightedScoreCalculator.classify_with_emoji(8.5)
        assert label == "Excelente"
        assert emoji == "⭐"

    def test_classify_with_emoji_imperdivel(self):
        label, emoji = WeightedScoreCalculator.classify_with_emoji(9.5, is_imperdivel_verified=True)
        assert label == "Imperdível"
        assert emoji == "🔥"
