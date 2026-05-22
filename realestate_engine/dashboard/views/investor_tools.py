"""Investor tools page for dashboard.

Provides interactive financial calculators:
- ROI & Yield simulator
- Mortgage calculator
- Risk assessment
- Investment comparison
"""
import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.investor_tools import InvestorTools


def render_investor_tools():
    """Render investor tools page."""
    st.title(" Ferramentas de Investidor")
    st.markdown("*Calculadoras financeiras para análise de investimento imobiliário*")

    tab1, tab2, tab3 = st.tabs([" ROI & Rendimento", " Simulador Crédito", " Análise Rápida"])

    #  Tab 1: ROI Calculator 
    with tab1:
        st.subheader(" Calculadora ROI & Rendimento")
        st.markdown("*Simule o retorno do seu investimento imobiliário*")

        col1, col2 = st.columns(2)

        with col1:
            purchase_price = st.number_input(
                "Preço de Compra (€)", min_value=10000, value=200000, step=5000,
                key="roi_price"
            )
            area = st.number_input(
                "Área (m²)", min_value=10, value=80, step=5, key="roi_area"
            )
            monthly_rent = st.number_input(
                "Renda Mensal Estimada (€)", min_value=0, value=0, step=50,
                help="Deixe 0 para estimar automaticamente",
                key="roi_rent"
            )
            renovation = st.number_input(
                "Custo de Renovação (€)", min_value=0, value=0, step=1000,
                key="roi_reno"
            )

        with col2:
            location_tier = st.selectbox(
                "Tipo de Zona",
                ["premium", "central", "good", "average", "peripheral"],
                format_func=lambda x: {
                    "premium": " Premium (Foz, Nevogilde)",
                    "central": " Central (Cedofeita, Boavista)",
                    "good": " Boa (Bonfim, Ramalde)",
                    "average": " Média (Campanha, Matosinhos)",
                    "peripheral": " Periférica (Gondomar, Valongo)",
                }[x],
                index=3,
                key="roi_tier"
            )
            holding_years = st.slider(
                "Período de Investimento (anos)", 1, 30, 5, key="roi_years"
            )
            appreciation = st.slider(
                "Valorização Anual (%)", 0.0, 15.0, 5.0, 0.5, key="roi_appr"
            )

        if st.button(" Calcular ROI", type="primary", width="stretch"):
            roi = InvestorTools.calculate_roi(
                purchase_price=purchase_price,
                estimated_monthly_rent=monthly_rent if monthly_rent > 0 else None,
                area_m2=area,
                location_tier=location_tier,
                renovation_cost=renovation,
                holding_period_years=holding_years,
                annual_appreciation_pct=appreciation,
            )

            if roi:
                st.markdown("---")
                st.subheader(" Resultados")

                # KPI row
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    color = "normal" if roi["gross_yield_pct"] < 5 else "off"
                    st.metric("Yield Bruto", f"{roi['gross_yield_pct']:.1f}%")
                with col_b:
                    st.metric("Yield Líquido", f"{roi['net_yield_pct']:.1f}%")
                with col_c:
                    st.metric("Cash-on-Cash", f"{roi['cash_on_cash_pct']:.1f}%")
                with col_d:
                    st.metric("ROI Anualizado", f"{roi['annualized_roi_pct']:.1f}%")

                # Detail section
                col_x, col_y = st.columns(2)
                with col_x:
                    st.markdown("** Rendimento**")
                    st.write(f"Renda mensal estimada: **{roi['estimated_monthly_rent']:,.0f}€**".replace(",", "."))
                    st.write(f"Rendimento anual bruto: {roi['annual_rent']:,.0f}€".replace(",", "."))
                    st.write(f"Custos anuais: {roi['annual_costs']:,.0f}€".replace(",", "."))
                    st.write(f"Rendimento líquido anual: **{roi['net_income']:,.0f}€**".replace(",", "."))

                with col_y:
                    st.markdown("** Investimento Total**")
                    st.write(f"Preço compra: {purchase_price:,.0f}€".replace(",", "."))
                    st.write(f"Custos aquisição (IMT+IS+Not.): {roi['acquisition_costs']:,.0f}€".replace(",", "."))
                    if renovation > 0:
                        st.write(f"Renovação: {renovation:,.0f}€".replace(",", "."))
                    st.write(f"**Investimento total: {roi['total_investment']:,.0f}€**".replace(",", "."))
                    st.write(f"Valor futuro ({holding_years}a): {roi['future_value']:,.0f}€".replace(",", "."))

                # Payback
                pb = roi["payback_years"]
                if pb < 100:
                    st.info(f"⏱ Payback estimado: **{pb:.1f} anos**")
                else:
                    st.warning(" Rendimento líquido negativo — investimento não gera cash flow positivo")

                # ROI verdict
                total_roi = roi["total_roi_pct"]
                if total_roi > 50:
                    st.success(f" ROI total em {holding_years} anos: **{total_roi:.0f}%** — Excelente investimento!")
                elif total_roi > 20:
                    st.success(f" ROI total em {holding_years} anos: **{total_roi:.0f}%** — Bom investimento")
                elif total_roi > 0:
                    st.info(f" ROI total em {holding_years} anos: **{total_roi:.0f}%** — Retorno moderado")
                else:
                    st.error(f" ROI total em {holding_years} anos: **{total_roi:.0f}%** — Investimento não recomendado")

    #  Tab 2: Mortgage Calculator 
    with tab2:
        st.subheader(" Simulador de Crédito Habitação")

        col1, col2 = st.columns(2)
        with col1:
            m_price = st.number_input("Preço do Imóvel (€)", min_value=10000, value=200000, step=5000, key="mort_price")
            m_down = st.slider("Entrada (%)", 5, 50, 20, key="mort_down")
        with col2:
            m_rate = st.slider("Taxa de Juro Anual (%)", 0.5, 8.0, 3.5, 0.1, key="mort_rate")
            m_term = st.slider("Prazo (anos)", 5, 40, 30, key="mort_term")

        if st.button(" Simular Crédito", type="primary", width="stretch"):
            mortgage = InvestorTools.calculate_mortgage(m_price, m_down, m_rate, m_term)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(" Prestação Mensal", f"{mortgage['monthly_payment']:,.0f}€".replace(",", "."))
            with col_b:
                st.metric(" Valor Financiado", f"{mortgage['loan_amount']:,.0f}€".replace(",", "."))
            with col_c:
                st.metric(" Entrada", f"{mortgage['down_payment']:,.0f}€".replace(",", "."))

            st.markdown("---")
            st.write(f"Total pago ao banco: **{mortgage['total_paid']:,.0f}€**".replace(",", "."))
            st.write(f"Total de juros: **{mortgage['total_interest']:,.0f}€**".replace(",", "."))
            st.write(f"Rácio juros/capital: {mortgage['interest_to_principal_ratio']:.1f}x")

            if mortgage['interest_to_principal_ratio'] > 1.5:
                st.warning(" Vai pagar mais em juros do que o capital emprestado. Considere um prazo mais curto.")

    #  Tab 3: Quick Analysis 
    with tab3:
        st.subheader(" Análise Rápida de Oportunidade")
        st.markdown("*Insira os dados de um imóvel para uma avaliação instantânea*")

        col1, col2 = st.columns(2)
        with col1:
            q_price = st.number_input("Preço (€)", min_value=10000, value=180000, step=5000, key="quick_price")
            q_area = st.number_input("Área (m²)", min_value=10, value=75, step=5, key="quick_area")
            q_rooms = st.number_input("Quartos", min_value=0, value=2, step=1, key="quick_rooms")
        with col2:
            q_freg = st.selectbox("Freguesia", [
                "Foz do Douro", "Nevogilde", "Aldoar", "Massarelos", "Lordelo do Ouro",
                "Cedofeita", "Santo Ildefonso", "Bonfim", "Paranhos", "Ramalde", "Campanha",
                "Matosinhos", "Leça da Palmeira", "Mafamude", "Canidelo",
            ], key="quick_freg")
            q_estado = st.selectbox("Estado", ["Novo", "Renovado", "Bom", "Usado", "Para Recuperar"], index=2, key="quick_estado")
            q_cert = st.selectbox("Certificado Energético", ["A+", "A", "B", "C", "D", "E", "F"], index=3, key="quick_cert")

        if st.button(" Analisar", type="primary", width="stretch"):
            from realestate_engine.valuation.ine_client import INEClient
            from realestate_engine.scoring.score_location_calculator import ScoreLocationCalculator

            ine = INEClient()
            price_m2 = q_price / q_area if q_area > 0 else 0

            # INE comparison
            data = ine.get_data_for_location(q_freg, "Porto")
            ine_median = data["median_price"]
            ratio = price_m2 / ine_median if ine_median > 0 else 1.0
            discount_vs_ine = (1 - ratio) * 100

            # Location score
            loc_score = ScoreLocationCalculator.calculate(freguesia=q_freg.lower(), concelho="porto")

            # ROI estimate
            tier_map = {
                "Foz do Douro": "premium", "Nevogilde": "premium",
                "Aldoar": "premium", "Massarelos": "central",
                "Cedofeita": "central", "Bonfim": "good",
            }
            tier = tier_map.get(q_freg, "average")
            roi = InvestorTools.calculate_roi(q_price, area_m2=q_area, location_tier=tier)

            st.markdown("---")

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("€/m²", f"{price_m2:,.0f}€".replace(",", "."))
            with col_b:
                delta_color = "normal" if discount_vs_ine > 0 else "inverse"
                st.metric("vs INE", f"{discount_vs_ine:+.0f}%", delta_color=delta_color)
            with col_c:
                st.metric(" Localização", f"{loc_score:.1f}/10")
            with col_d:
                st.metric(" Yield Bruto", f"{roi.get('gross_yield_pct', 0):.1f}%")

            if discount_vs_ine > 10:
                st.success(f" **{discount_vs_ine:.0f}% abaixo** da mediana INE ({ine_median:,.0f}€/m²) — Potencial oportunidade!")
            elif discount_vs_ine > 0:
                st.info(f" {discount_vs_ine:.0f}% abaixo da mediana INE — Preço competitivo")
            elif discount_vs_ine > -10:
                st.warning(f" {abs(discount_vs_ine):.0f}% acima da mediana INE — Preço de mercado")
            else:
                st.error(f" {abs(discount_vs_ine):.0f}% acima da mediana INE — Sobrevalorizado")
