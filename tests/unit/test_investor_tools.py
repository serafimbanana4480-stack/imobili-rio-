"""Unit tests for InvestorTools financial calculations."""

from realestate_engine.investor_tools import InvestorTools


def test_calculate_deal_profit_includes_net_and_risk_adjusted_profit():
    result = InvestorTools.calculate_deal_profit(
        purchase_price=250000.0,
        estimated_sale_price=300000.0,
        estimated_monthly_rent=1200.0,
        area_m2=90.0,
        location_tier="central",
        renovation_cost=15000.0,
        holding_period_years=5,
        annual_appreciation_pct=4.0,
        selling_cost_pct=0.05,
        financing_cost_pct=0.02,
    )

    assert result["gross_profit"] > 0
    assert result["net_profit"] <= result["gross_profit"]
    assert "risk_adjusted_profit" in result
    assert isinstance(result["risk_adjusted_profit"], (int, float))
    assert result["holding_costs"] > 0
    assert result["sale_costs"] > 0
    assert result["financing_costs"] > 0


def test_calculate_deal_profit_handles_invalid_purchase_price():
    assert InvestorTools.calculate_deal_profit(0) == {}
