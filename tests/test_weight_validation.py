"""Tests for weight validation from Phase 5 Scoring Engine Audit."""
import pytest
import math
from realestate_engine.scoring.weighted_score_calculator import (
    WeightedScoreCalculator,
    WeightValidationError,
    WeightConfig
)


class TestWeightValidation:
    """Test suite for weight validation."""

    def test_default_weights(self):
        """Test default weights are valid."""
        calculator = WeightedScoreCalculator()
        
        # Check weights sum to 1.0
        total = sum(calculator.weights.values())
        assert math.isclose(total, 1.0, rel_tol=0.05)
        
        # Check all weights are in valid range
        for weight in calculator.weights.values():
            assert 0.0 <= weight <= 1.0
        
        # Check no single weight dominates
        max_weight = max(calculator.weights.values())
        assert max_weight <= 0.6

    def test_valid_custom_weights(self):
        """Test validation of valid custom weights."""
        valid_weights = {
            "discount": 0.25,
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
        }
        
        calculator = WeightedScoreCalculator(weights=valid_weights)
        
        assert calculator.weights == valid_weights
        assert calculator.current_config is not None
        assert calculator.current_config.validated_by == "system"

    def test_invalid_weights_sum(self):
        """Test validation rejects weights that don't sum to 1.0."""
        invalid_weights = {
            "discount": 0.50,
            "location": 0.30,
            "condition": 0.15,
            "amenities": 0.10,
            "liquidity": 0.05,
            "freshness": 0.10,  # Sum = 1.2 (invalid)
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "sum to 1.0" in str(exc_info.value).lower()

    def test_invalid_weights_range(self):
        """Test validation rejects weights outside [0, 1] range."""
        invalid_weights = {
            "discount": 1.5,  # Invalid: > 1.0
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "must be in" in str(exc_info.value).lower()

    def test_invalid_weights_negative(self):
        """Test validation rejects negative weights."""
        invalid_weights = {
            "discount": -0.10,  # Invalid: negative
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "must be in" in str(exc_info.value).lower()

    def test_invalid_single_weight_dominance(self):
        """Test validation rejects weights where single factor dominates."""
        invalid_weights = {
            "discount": 0.70,  # Invalid: > 0.6 max
            "location": 0.10,
            "condition": 0.05,
            "amenities": 0.05,
            "liquidity": 0.05,
            "freshness": 0.05,
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "exceed" in str(exc_info.value).lower()

    def test_missing_required_weight(self):
        """Test validation rejects missing required weights."""
        invalid_weights = {
            "discount": 0.20,
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            # Missing "freshness"
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "missing" in str(exc_info.value).lower()

    def test_extra_unexpected_weight(self):
        """Test validation rejects unexpected weights."""
        invalid_weights = {
            "discount": 0.20,
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
            "extra_factor": 0.05,  # Invalid: unexpected
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "unexpected" in str(exc_info.value).lower()

    def test_non_numeric_weight(self):
        """Test validation rejects non-numeric weights."""
        invalid_weights = {
            "discount": "0.20",  # Invalid: string instead of float
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
        }
        
        with pytest.raises(WeightValidationError) as exc_info:
            WeightedScoreCalculator(weights=invalid_weights)
        
        assert "must be numeric" in str(exc_info.value).lower()

    def test_weight_config_checksum(self):
        """Test checksum calculation for weight configuration."""
        calculator = WeightedScoreCalculator()
        config = calculator.get_current_config()
        
        assert config is not None
        assert config.checksum is not None
        assert len(config.checksum) == 64  # SHA256 hex string
        assert isinstance(config.checksum, str)

    def test_update_weights_with_validation(self):
        """Test weight update with validation and audit trail."""
        calculator = WeightedScoreCalculator()
        
        new_weights = {
            "discount": 0.25,
            "location": 0.25,
            "condition": 0.15,
            "amenities": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
        }
        
        # Update weights
        calculator.update_weights(
            new_weights,
            changed_by="test_user",
            reason="Testing weight update"
        )
        
        # Verify weights updated
        assert calculator.weights == new_weights
        
        # Verify config updated
        config = calculator.get_current_config()
        assert config.validated_by == "test_user"
        assert config.weights == new_weights

    def test_update_weights_invalid(self):
        """Test weight update rejects invalid weights."""
        calculator = WeightedScoreCalculator()
        
        invalid_weights = {
            "discount": 0.90,  # Invalid: too high
            "location": 0.05,
            "condition": 0.05,
            "amenities": 0.05,
            "liquidity": 0.05,
            "freshness": 0.05,
        }
        
        # Should raise validation error
        with pytest.raises(WeightValidationError):
            calculator.update_weights(
                invalid_weights,
                changed_by="test_user",
                reason="Testing invalid update"
            )
        
        # Original weights should remain unchanged
        original_weights = calculator.DEFAULT_WEIGHTS.copy()
        assert calculator.weights == original_weights

    def test_calculate_score(self):
        """Test score calculation with weighted factors."""
        calculator = WeightedScoreCalculator()
        
        scores = {
            "discount": 8.0,
            "location": 7.0,
            "condition": 9.0,
            "amenities": 6.0,
            "liquidity": 7.0,
            "freshness": 8.0,
        }
        
        final_score = calculator.calculate(scores)
        
        # Score should be between 0 and 10
        assert 0.0 <= final_score <= 10.0
        assert isinstance(final_score, float)

    def test_calculate_score_missing_factor(self):
        """Test score calculation with missing factor (uses default 5.0)."""
        calculator = WeightedScoreCalculator()
        
        scores = {
            "discount": 8.0,
            "location": 7.0,
            "condition": 9.0,
            "amenities": 6.0,
            "liquidity": 7.0,
            # Missing "freshness"
        }
        
        final_score = calculator.calculate(scores)
        
        # Should still calculate score with default for missing factor
        assert 0.0 <= final_score <= 10.0

    def test_classify_score(self):
        """Test score classification."""
        assert WeightedScoreCalculator.classify(9.5, is_imperdivel_verified=True) == "Imperdível"
        assert WeightedScoreCalculator.classify(9.5, is_imperdivel_verified=False) == "Excelente"
        assert WeightedScoreCalculator.classify(8.0) == "Excelente"
        assert WeightedScoreCalculator.classify(6.5) == "Bom"
        assert WeightedScoreCalculator.classify(5.0) == "Aceitável"
        assert WeightedScoreCalculator.classify(3.5) == "Abaixo da média"
        assert WeightedScoreCalculator.classify(2.0) == "Não recomendado"

    def test_is_imperdivel(self):
        """Test Imperdível classification logic."""
        # Should be Imperdível
        assert WeightedScoreCalculator.is_imperdivel(
            score=9.5,
            discount_pct=20.0,
            has_any_flags=False
        ) == True
        
        # Should NOT be Imperdível (score too low)
        assert WeightedScoreCalculator.is_imperdivel(
            score=8.5,
            discount_pct=20.0,
            has_any_flags=False
        ) == False
        
        # Should NOT be Imperdível (discount too low)
        assert WeightedScoreCalculator.is_imperdivel(
            score=9.5,
            discount_pct=10.0,
            has_any_flags=False
        ) == False
        
        # Should NOT be Imperdível (has red flags)
        assert WeightedScoreCalculator.is_imperdivel(
            score=9.5,
            discount_pct=20.0,
            has_any_flags=True
        ) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
