"""Unit tests for ScoreConditionCalculator."""
import pytest
from realestate_engine.scoring.score_condition_calculator import ScoreConditionCalculator


class TestScoreConditionCalculator:
    """Test condition score calculator."""

    def test_calculate_novo(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado="novo", ano_construcao=2020, cert_energetico="A+")
        assert score > 7  # New property should score high

    def test_calculate_renovado(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado="renovado", ano_construcao=2010, cert_energetico="B")
        assert score > 5  # Renovated should score good

    def test_calculate_usado(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado="usado", ano_construcao=1990, cert_energetico="D")
        assert score < 7  # Used property should score lower

    def test_calculate_para_recuperar(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado="para_recuperar", ano_construcao=1970, cert_energetico="G")
        assert score < 3  # Needs renovation should score low

    def test_calculate_missing_data(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado=None, ano_construcao=None, cert_energetico=None)
        assert 0 <= score <= 10

    def test_calculate_old_but_good_condition(self):
        calc = ScoreConditionCalculator()
        score = calc.calculate(estado="bom", ano_construcao=1950, cert_energetico="C")
        assert score > 3  # Old but in good condition should score decent

    def test_calculate_energy_cert_impact(self):
        calc = ScoreConditionCalculator()
        score_a = calc.calculate(estado="usado", ano_construcao=2010, cert_energetico="A+")
        score_g = calc.calculate(estado="usado", ano_construcao=2010, cert_energetico="G")
        assert score_a > score_g  # Better energy cert should score higher
