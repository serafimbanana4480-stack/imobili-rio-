"""Unit tests for ScoreLocationCalculator."""
import pytest
from realestate_engine.scoring.score_location_calculator import ScoreLocationCalculator


class TestScoreLocationCalculator:
    """Test location score calculator."""

    def test_calculate_good_location(self):
        calc = ScoreLocationCalculator()
        # Test with good location (Cedofeita, Porto)
        score = calc.calculate(
            freguesia="Cedofeita",
            concelho="Porto",
            ine_tendencia=0.5,
            dist_metro=200.0,
            dist_escola=300.0,
            dist_comercio=100.0,
        )
        assert 0 <= score <= 10
        assert score > 5  # Should be good location

    def test_calculate_poor_location(self):
        calc = ScoreLocationCalculator()
        # Test with poor location
        score = calc.calculate(
            freguesia="Unknown",
            concelho="Unknown",
            ine_tendencia=-0.5,
            dist_metro=5000.0,
            dist_escola=5000.0,
            dist_comercio=5000.0,
        )
        assert 0 <= score <= 10
        assert score < 5  # Should be poor location

    def test_calculate_missing_ine_data(self):
        calc = ScoreLocationCalculator()
        # Test with missing INE data
        score = calc.calculate(
            freguesia="Cedofeita",
            concelho="Porto",
            ine_tendencia=None,
        )
        assert 0 <= score <= 10

    def test_calculate_missing_poi_data(self):
        calc = ScoreLocationCalculator()
        # Test with missing POI data
        score = calc.calculate(
            freguesia="Cedofeita",
            concelho="Porto",
            ine_tendencia=0.5,
            dist_metro=None,
            dist_escola=None,
            dist_comercio=None,
        )
        assert 0 <= score <= 10

    def test_calculate_missing_coordinates_keeps_neutral_location_context(self):
        calc = ScoreLocationCalculator()
        score = calc.calculate(
            freguesia="Cedofeita",
            concelho="Porto",
            ine_tendencia=0.5,
            dist_metro=200.0,
            dist_escola=300.0,
            dist_comercio=100.0,
            lat=None,
            lon=None,
        )
        assert 0 <= score <= 10
        assert score > 6.0

    def test_calculate_lisbon_location_scores_above_neutral(self):
        calc = ScoreLocationCalculator()
        score = calc.calculate(
            freguesia="Avenidas Novas",
            concelho="Lisboa",
            ine_tendencia=0.4,
            dist_metro=350.0,
            dist_escola=450.0,
            dist_comercio=180.0,
        )
        assert 0 <= score <= 10
        assert score > 5.5

    def test_calculate_unknown_location_remains_neutral(self):
        calc = ScoreLocationCalculator()
        score = calc.calculate(
            freguesia="Localidade Desconhecida",
            concelho="Concelho Inexistente",
        )
        print(f"DEBUG: Unknown location score: {score}")
        assert 0 <= score <= 10
        # Should be around 5.0 or 6.0 depending on weights, but definitely not 10.0 or 0.0
        assert 4.0 <= score <= 7.0
