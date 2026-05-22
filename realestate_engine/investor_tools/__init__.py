"""Investor analytics tools for the Real Estate Opportunity Engine.

Provides financial calculations for real estate investors:
- ROI & Cash-on-Cash Return
- Cash flow simulation (rental yield)
- Internal Rate of Return (IRR)
- Risk assessment (market liquidity, price volatility)
- Financing calculator
"""
import math
from typing import Dict, Optional, List
from loguru import logger


class InvestorTools:
    """Financial analysis tools for property investment evaluation."""

    # ── Porto rental market reference data (2025-2026) ──────────────────
    # Average monthly rent per m² by area type
    RENT_REFERENCE_M2 = {
        "premium": 16.0,    # Foz, Nevogilde, Aldoar
        "central": 13.5,    # Cedofeita, Boavista, Massarelos
        "good": 11.5,       # Bonfim, Ramalde, Paranhos
        "average": 9.5,     # Campanha, Matosinhos, Gaia
        "peripheral": 7.5,  # Gondomar, Valongo, Maia
    }

    # Annual costs as % of property value
    DEFAULT_COSTS = {
        "imt_pct": 0.065,          # IMT (Imposto Municipal Transações) ~6.5%
        "stamp_duty_pct": 0.008,   # Imposto Selo
        "notary_pct": 0.015,       # Notário + Registo
        "condominio_monthly": 80,  # Average monthly condominium
        "imi_annual_pct": 0.004,   # IMI (municipal tax) ~0.4%
        "insurance_annual_pct": 0.003,  # Insurance
        "maintenance_annual_pct": 0.01, # Maintenance reserve
        "vacancy_rate_pct": 0.05,  # 5% vacancy rate
        "management_pct": 0.10,    # Property management fee
    }

    @classmethod
    def calculate_deal_profit(
        cls,
        purchase_price: float,
        estimated_sale_price: Optional[float] = None,
        estimated_monthly_rent: Optional[float] = None,
        area_m2: Optional[float] = None,
        location_tier: str = "average",
        renovation_cost: float = 0,
        holding_period_years: int = 5,
        annual_appreciation_pct: float = 5.0,
        selling_cost_pct: float = 0.05,
        financing_cost_pct: float = 0.0,
    ) -> Dict:
        """Calculate a more realistic deal profit and risk-adjusted return.

        This keeps the old ROI helper intact, but exposes a clearer metric for
        dashboards and opportunity selection:
        - gross profit: fair value minus asking price
        - net profit: gross profit minus acquisition/holding/sale costs
        - risk-adjusted profit: net profit dampened by uncertainty and leverage costs
        """
        if purchase_price <= 0:
            return {}

        roi = cls.calculate_roi(
            purchase_price=purchase_price,
            estimated_monthly_rent=estimated_monthly_rent,
            area_m2=area_m2,
            location_tier=location_tier,
            renovation_cost=renovation_cost,
            holding_period_years=holding_period_years,
            annual_appreciation_pct=annual_appreciation_pct,
        )

        if not roi:
            return {}

        fair_value = estimated_sale_price if estimated_sale_price and estimated_sale_price > 0 else roi.get("future_value", 0)
        gross_profit = fair_value - purchase_price

        acquisition_costs = roi.get("acquisition_costs", 0)
        annual_costs = roi.get("annual_costs", 0)
        holding_costs = annual_costs * max(1, holding_period_years)
        sale_costs = fair_value * selling_cost_pct
        financing_costs = purchase_price * financing_cost_pct

        net_profit = gross_profit - acquisition_costs - holding_costs - renovation_cost - sale_costs - financing_costs

        risk_factor = 1.0
        if roi.get("annualized_roi_pct", 0) < 5:
            risk_factor *= 0.85
        if roi.get("payback_years", float("inf")) > 10:
            risk_factor *= 0.90

        confidence_factor = 1.0
        if roi.get("net_yield_pct", 0) < 2:
            confidence_factor *= 0.85
        elif roi.get("net_yield_pct", 0) > 6:
            confidence_factor *= 1.05

        risk_adjusted_profit = net_profit * risk_factor * confidence_factor

        roi.update({
            "gross_profit": round(gross_profit, 0),
            "net_profit": round(net_profit, 0),
            "risk_adjusted_profit": round(risk_adjusted_profit, 0),
            "holding_costs": round(holding_costs, 0),
            "sale_costs": round(sale_costs, 0),
            "financing_costs": round(financing_costs, 0),
        })
        return roi

    @classmethod
    def calculate_roi(
        cls,
        purchase_price: float,
        estimated_monthly_rent: Optional[float] = None,
        area_m2: Optional[float] = None,
        location_tier: str = "average",
        renovation_cost: float = 0,
        holding_period_years: int = 5,
        annual_appreciation_pct: float = 5.0,
    ) -> Dict:
        """Calculate comprehensive ROI metrics.

        Returns:
            Dict with gross_yield, net_yield, cash_on_cash, total_roi,
            annualized_roi, payback_years.
        """
        if purchase_price <= 0:
            return {}

        # Estimate rent if not provided
        if not estimated_monthly_rent:
            if area_m2 and area_m2 > 0:
                rent_m2 = cls.RENT_REFERENCE_M2.get(location_tier, 9.5)
                estimated_monthly_rent = area_m2 * rent_m2
            else:
                estimated_monthly_rent = purchase_price * 0.004  # ~0.4% monthly

        annual_rent = estimated_monthly_rent * 12

        # ── Gross yield ─────────────────────────────────────────────────
        gross_yield = (annual_rent / purchase_price) * 100

        # ── Annual costs ────────────────────────────────────────────────
        annual_costs = (
            cls.DEFAULT_COSTS["condominio_monthly"] * 12 +
            purchase_price * cls.DEFAULT_COSTS["imi_annual_pct"] +
            purchase_price * cls.DEFAULT_COSTS["insurance_annual_pct"] +
            purchase_price * cls.DEFAULT_COSTS["maintenance_annual_pct"] +
            annual_rent * cls.DEFAULT_COSTS["management_pct"]
        )

        # ── Net operating income ────────────────────────────────────────
        effective_rent = annual_rent * (1 - cls.DEFAULT_COSTS["vacancy_rate_pct"])
        net_income = effective_rent - annual_costs
        net_yield = (net_income / purchase_price) * 100

        # ── Acquisition costs ───────────────────────────────────────────
        acquisition_costs = purchase_price * (
            cls.DEFAULT_COSTS["imt_pct"] +
            cls.DEFAULT_COSTS["stamp_duty_pct"] +
            cls.DEFAULT_COSTS["notary_pct"]
        )
        total_investment = purchase_price + acquisition_costs + renovation_cost

        # ── Cash-on-Cash return ─────────────────────────────────────────
        cash_on_cash = (net_income / total_investment) * 100

        # ── Total ROI with appreciation ─────────────────────────────────
        future_value = purchase_price * (1 + annual_appreciation_pct / 100) ** holding_period_years
        total_rent_income = net_income * holding_period_years
        total_gain = (future_value - purchase_price) + total_rent_income
        total_roi = (total_gain / total_investment) * 100
        annualized_roi = ((1 + total_gain / total_investment) ** (1 / holding_period_years) - 1) * 100

        # ── Payback period ──────────────────────────────────────────────
        payback_years = total_investment / net_income if net_income > 0 else float("inf")

        return {
            "estimated_monthly_rent": round(estimated_monthly_rent, 0),
            "annual_rent": round(annual_rent, 0),
            "annual_costs": round(annual_costs, 0),
            "net_income": round(net_income, 0),
            "gross_yield_pct": round(gross_yield, 2),
            "net_yield_pct": round(net_yield, 2),
            "acquisition_costs": round(acquisition_costs, 0),
            "total_investment": round(total_investment, 0),
            "cash_on_cash_pct": round(cash_on_cash, 2),
            "total_roi_pct": round(total_roi, 2),
            "annualized_roi_pct": round(annualized_roi, 2),
            "payback_years": round(payback_years, 1),
            "future_value": round(future_value, 0),
        }

    @staticmethod
    def calculate_irr(
        initial_investment: float,
        annual_cash_flows: List[float],
        terminal_value: float = 0,
    ) -> Optional[float]:
        """Calculate Internal Rate of Return using Newton's method.

        Args:
            initial_investment: Total investment (negative cash flow)
            annual_cash_flows: List of annual net income
            terminal_value: Sale price at end of holding period
        """
        # Add terminal value to last cash flow
        cash_flows = [-initial_investment] + list(annual_cash_flows)
        if terminal_value > 0:
            cash_flows[-1] += terminal_value

        # Newton-Raphson method
        rate = 0.10  # Initial guess
        for _ in range(100):
            npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
            dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows))

            if abs(dnpv) < 1e-10:
                # Derivative is near zero - check if NPV is also near zero (converged)
                if abs(npv) < 1e-6:
                    return round(rate * 100, 2)
                else:
                    # Cannot converge with near-zero derivative
                    break

            new_rate = rate - npv / dnpv
            if abs(new_rate - rate) < 1e-6:
                return round(new_rate * 100, 2)
            rate = new_rate

        return round(rate * 100, 2) if -1 < rate < 10 else None

    @staticmethod
    def calculate_mortgage(
        purchase_price: float,
        down_payment_pct: float = 20.0,
        interest_rate_pct: float = 3.5,
        term_years: int = 30,
    ) -> Dict:
        """Calculate mortgage details."""
        loan_amount = purchase_price * (1 - down_payment_pct / 100)
        monthly_rate = interest_rate_pct / 100 / 12
        n_payments = term_years * 12

        if monthly_rate > 0:
            monthly_payment = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** n_payments
            ) / ((1 + monthly_rate) ** n_payments - 1)
        else:
            monthly_payment = loan_amount / n_payments

        total_paid = monthly_payment * n_payments
        total_interest = total_paid - loan_amount

        return {
            "loan_amount": round(loan_amount, 0),
            "down_payment": round(purchase_price * down_payment_pct / 100, 0),
            "monthly_payment": round(monthly_payment, 2),
            "total_paid": round(total_paid, 0),
            "total_interest": round(total_interest, 0),
            "interest_to_principal_ratio": round(total_interest / loan_amount, 2) if loan_amount > 0 else 0,
        }

    @staticmethod
    def assess_risk(
        listing: Dict,
        valuation: Optional[Dict] = None,
        market_context: Optional[Dict] = None,
    ) -> Dict:
        """Assess investment risk for a property.

        Returns risk score 1-10 (1=very low risk, 10=very high risk) and factors.
        """
        risk_score = 5.0
        factors = []

        # Valuation confidence
        if valuation:
            conf = valuation.get("confianca", 0.5)
            if conf < 0.3:
                risk_score += 2.0
                factors.append("Baixa confiança na avaliação — poucos comparáveis")
            elif conf < 0.5:
                risk_score += 1.0
                factors.append("Confiança moderada na avaliação")
            elif conf >= 0.8:
                risk_score -= 1.0
                factors.append("Alta confiança na avaliação")

        # Market activity
        if market_context:
            activity = market_context.get("market_activity", "moderado")
            if activity == "muito ativo":
                risk_score -= 1.0
                factors.append("Mercado muito ativo — boa liquidez")
            elif activity == "baixo":
                risk_score += 1.5
                factors.append("Mercado pouco ativo — risco de iliquidez")

        # Property age risk
        ano = listing.get("ano_construcao")
        estado = (listing.get("estado") or "").lower()
        if ano and ano < 1960 and estado not in ("renovado", "remodelado", "novo"):
            risk_score += 1.5
            factors.append(f"Edifício de {ano} sem renovação — risco de obras imprevistas")

        # Location stability
        freg = (listing.get("freguesia") or "").lower()
        premium_zones = {"foz do douro", "nevogilde", "massarelos", "aldoar"}
        if freg in premium_zones:
            risk_score -= 0.5
            factors.append("Zona premium — baixa volatilidade")

        # Price/m² vs market
        preco_m2 = listing.get("preco_por_m2")
        ine_m2 = listing.get("ine_preco_medio_m2")
        if preco_m2 and ine_m2 and ine_m2 > 0:
            ratio = preco_m2 / ine_m2
            if ratio > 1.3:
                risk_score += 1.5
                factors.append(f"Preço {(ratio-1)*100:.0f}% acima da mediana — risco de sobrevalorização")
            elif ratio < 0.7:
                risk_score += 0.5
                factors.append("Preço muito abaixo do mercado — verificar razões")

        risk_score = max(1.0, min(10.0, risk_score))

        risk_level = (
            "Muito Baixo" if risk_score <= 3 else
            "Baixo" if risk_score <= 4.5 else
            "Moderado" if risk_score <= 6 else
            "Alto" if risk_score <= 7.5 else
            "Muito Alto"
        )

        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "factors": factors,
        }
