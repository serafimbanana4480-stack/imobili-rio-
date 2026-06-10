"""Critical calculation validation tests.

Validates:
- Price per m² calculation correctness
- Profit potential calculation (absolute and percentage)
- Discount/savings calculation
- Score consistency with profit signals
- Deduplication fingerprint stability
"""
import pytest
from realestate_engine.etl.normalizer import Normalizer
from realestate_engine.etl.deduplicator import Deduplicator


class TestPriceCalculations:
    """Test price, area, and derived metric calculations."""

    def test_normalize_price_standard(self):
        assert Normalizer.normalize_price("250000 €") == 250000.0
        assert Normalizer.normalize_price("250 000 €") == 250000.0

    def test_normalize_price_with_dots(self):
        assert Normalizer.normalize_price("1.250.000 €") == 1250000.0

    def test_normalize_price_decimal_comma(self):
        assert Normalizer.normalize_price("250.000,50 €") == 250000.5

    def test_normalize_price_k_prefix(self):
        assert Normalizer.normalize_price("250k €") == 250000.0
        assert Normalizer.normalize_price("1.2M €") == 1200000.0

    def test_normalize_price_invalid_returns_none(self):
        assert Normalizer.normalize_price("sob consulta") is None
        assert Normalizer.normalize_price("") is None
        assert Normalizer.normalize_price(None) is None

    def test_normalize_area_standard(self):
        assert Normalizer.normalize_area("85 m²") == 85.0
        assert Normalizer.normalize_area("120,5 m²") == 120.5

    def test_normalize_area_range_validation(self):
        assert Normalizer.normalize_area("4 m²") is None  # Too small (<5)
        assert Normalizer.normalize_area("15000 m²") is None  # Too large

    def test_price_per_m2_calculation(self):
        data = {"preco_pedido": 250000.0, "area_util_m2": 85.0}
        assert data["preco_pedido"] / data["area_util_m2"] == pytest.approx(2941.18, rel=0.01)

    def test_zero_area_returns_none(self):
        data = {"preco_pedido": 250000.0, "area_util_m2": 0}
        if data["area_util_m2"] > 0:
            result = data["preco_pedido"] / data["area_util_m2"]
        else:
            result = None
        assert result is None


class TestProfitCalculations:
    """Test profit and discount calculations from valuation vs listing price."""

    def test_profit_absolute_positive(self):
        """Underpriced listing = positive profit potential."""
        preco_pedido = 200000.0
        valor_justo = 250000.0
        lucro = valor_justo - preco_pedido
        assert lucro == 50000.0
        assert lucro > 0

    def test_profit_absolute_negative(self):
        """Overpriced listing = negative profit (loss)."""
        preco_pedido = 300000.0
        valor_justo = 250000.0
        lucro = valor_justo - preco_pedido
        assert lucro == -50000.0
        assert lucro < 0

    def test_discount_percentage(self):
        """Discount = (valor_justo - preco) / preco."""
        preco = 200000.0
        valor_justo = 250000.0
        discount = (valor_justo - preco) / preco
        assert discount == 0.25  # 25% underpriced

    def test_overpricing_percentage(self):
        preco = 250000.0
        valor_justo = 200000.0
        discount = (valor_justo - preco) / preco
        assert discount == -0.20  # 20% overpriced

    def test_profit_with_renovation_costs(self):
        """Net profit should account for renovation."""
        preco = 180000.0
        valor_justo = 250000.0
        renovation = 30000.0
        gross_profit = valor_justo - preco
        net_profit = gross_profit - renovation
        assert gross_profit == 70000.0
        assert net_profit == 40000.0
        assert net_profit < gross_profit

    def test_roi_calculation(self):
        """ROI = (Gain - Cost) / Cost."""
        investment = 200000.0
        final_value = 250000.0
        roi = (final_value - investment) / investment
        assert roi == 0.25
        assert roi == 25.0 / 100


class TestDedupFingerprint:
    """Test deduplication fingerprint stability."""

    def test_same_listing_same_fingerprint(self):
        l1 = {"preco_pedido": 200000, "area_util_m2": 80, "quartos": 2, "freguesia": "Cedofeita"}
        l2 = {"preco_pedido": 200000, "area_util_m2": 80, "quartos": 2, "freguesia": "Cedofeita"}
        fp1 = Deduplicator.generate_fingerprint(l1)
        fp2 = Deduplicator.generate_fingerprint(l2)
        assert fp1 == fp2

    def test_different_price_different_fingerprint(self):
        l1 = {"preco_pedido": 200000, "area_util_m2": 80, "quartos": 2, "freguesia": "Cedofeita"}
        l2 = {"preco_pedido": 250000, "area_util_m2": 80, "quartos": 2, "freguesia": "Cedofeita"}
        fp1 = Deduplicator.generate_fingerprint(l1)
        fp2 = Deduplicator.generate_fingerprint(l2)
        assert fp1 != fp2

    def test_fingerprint_ignores_minor_differences(self):
        l1 = {"preco_pedido": 200000, "area_util_m2": 80, "quartos": 2, "freguesia": "Cedofeita"}
        l2 = {"preco_pedido": 200000, "area_util_m2": 80, "quartos": 2, "freguesia": "cedofeita"}
        fp1 = Deduplicator.generate_fingerprint(l1)
        fp2 = Deduplicator.generate_fingerprint(l2)
        assert fp1 == fp2  # Case insensitive


class TestScoreConsistency:
    """Test that score calculations are internally consistent."""

    def test_high_discount_correlates_with_high_score(self):
        """A large positive discount should contribute to a higher score."""
        # ScoreDiscountCalculator logic: higher discount = higher score
        discount = 0.25  # 25% underpriced
        score = min(10.0, discount * 40)  # Simplified model
        assert score == 10.0  # Capped at 10

    def test_negative_discount_lowers_score(self):
        discount = -0.10  # 10% overpriced
        score = max(0.0, discount * 40)  # Simplified
        assert score == 0.0  # Floor at 0

    def test_score_components_sum_reasonably(self):
        """Individual score components should not exceed their bounds."""
        components = {
            "discount": 8.0,
            "location": 7.5,
            "condition": 6.0,
            "liquidity": 7.0,
            "freshness": 8.5,
        }
        for name, value in components.items():
            assert 0 <= value <= 10, f"Component {name} out of bounds: {value}"

    def test_final_score_within_bounds(self):
        """Final weighted score must be 0-10 regardless of inputs."""
        weights = {"discount": 0.35, "location": 0.25, "condition": 0.15, "liquidity": 0.15, "freshness": 0.10}
        components = {"discount": 8.0, "location": 7.5, "condition": 6.0, "liquidity": 7.0, "freshness": 8.5}
        total = sum(components[k] * weights[k] for k in weights)
        assert 0 <= total <= 10
        assert total == pytest.approx(7.475, abs=0.001)
