"""Overview page for dashboard — Porto Real Estate Engine.

Investment-focused redesign:
- Financial KPIs at top (profit margin, ROI potential, opportunity count)
- Top opportunities as hero cards with profit prominently displayed
- Color-coded profit indicators (green=profit, red=loss)
- Quick-action filters for investors
- Market health indicators
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import statistics
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.dashboard.utils.theme import (
    profit_color,
    score_badge,
    TEXT_COLOR_MUTED_DARK,
    BORDER_COLOR_DARK,
    TEXT_COLOR_DARK,
    PRIMARY_COLOR,
)
from realestate_engine.dashboard.utils.formatting import (
    format_currency,
    format_percentage,
    format_area,
    format_price_per_m2,
    format_number
)


def render_overview():
    """Render investment-focused overview dashboard."""
    st.title(" Porto Real Estate Intelligence")
    st.markdown(f"<p style='color:{TEXT_COLOR_MUTED_DARK};font-size:1.1em;margin-top:-10px;'>Painel de decisão para investimento imobiliário — oportunidades em tempo real</p>", unsafe_allow_html=True)

    try:
        repo = DatabaseRepository()

        # Watchlist link
        st.sidebar.markdown("---")
        st.sidebar.markdown("###  Minha Watchlist")
        watchlist_count = len(repo.get_watchlist())
        st.sidebar.metric("Propriedades guardadas", f"{watchlist_count}")

        #  Load Data 
        with st.spinner("A carregar dados..."):
            all_listings = repo.get_clean_listings(limit=10000)
            total = repo.get_total_clean_listings_count()

            # Get scored listings with valuations
            top_scores = repo.get_top_scores(min_score=8.0, limit=500)
            excellent_scores = repo.get_top_scores(min_score=7.0, limit=500)
            all_scores = repo.get_top_scores(min_score=0.0, limit=5000)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Por favor, tente novamente ou verifique a conexão com a base de dados.")
        return

    #  FINANCIAL KPIs Row 
    st.markdown("###  Indicadores Financeiros do Mercado")

    # Calculate aggregate investment metrics
    profit_listings = []
    avg_discount_pct = None
    median_discount_pct = None
    total_potential_profit = 0
    opportunities_count = 0

    if all_scores:
        for score in all_scores:
            l = score.listing
            if not l or not l.valuations:
                continue
            val = l.valuations[0]
            if val.valor_justo and l.preco_pedido and l.preco_pedido > 0:
                discount = (val.valor_justo - l.preco_pedido) / l.preco_pedido
                profit = val.valor_justo - l.preco_pedido
                if discount > 0:
                    opportunities_count += 1
                    total_potential_profit += profit
                profit_listings.append({
                    "discount_pct": discount * 100,
                    "profit": profit,
                    "score": score.score_total,
                })

        if profit_listings:
            discounts = [p["discount_pct"] for p in profit_listings]
            avg_discount_pct = statistics.mean(discounts)
            median_discount_pct = statistics.median(discounts)

    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)

    with col_kpi1:
        st.metric(
            label=" Total Anúncios",
            value=format_number(total),
            delta=f"{opportunities_count} oportunidades" if opportunities_count else None,
            delta_color="normal" if opportunities_count else "off"
        )

    with col_kpi2:
        st.metric(
            label=" Imperdíveis (8+)",
            value=len(top_scores),
            delta=None
        )

    with col_kpi3:
        st.metric(
            label=" Excelentes (≥7.5)",
            value=len(excellent_scores),
            delta=None
        )

    with col_kpi4:
        if avg_discount_pct is not None:
            st.metric(
                label=" Desconto Médio",
                value=format_percentage(avg_discount_pct / 100),
                delta=f"mediana {format_percentage(median_discount_pct / 100)}" if median_discount_pct else None,
                delta_color="inverse"
            )
        else:
            st.metric(label=" Desconto Médio", value="N/A")

    with col_kpi5:
        if total_potential_profit > 0:
            st.metric(
                label=" Lucro Potencial Total",
                value=format_currency(total_potential_profit),
                delta=None
            )
        else:
            st.metric(label=" Lucro Potencial Total", value="N/A")

    #  Quick Action Filters 
    st.markdown("---")
    st.markdown("###  Filtros Rápidos para Investidores")

    qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
    with qcol1:
        if st.button(" Melhores Oportunidades", width="stretch", type="primary"):
            st.session_state['min_score'] = 7.5
            st.session_state['max_price'] = 500000
            st.session_state['page'] = " Pesquisar"
            st.rerun()
    with qcol2:
        if st.button(" T2 Porto Centro", width="stretch"):
            st.session_state['tipologia'] = "T2"
            st.session_state['freguesia'] = "Cedofeita"
            st.session_state['page'] = " Pesquisar"
            st.rerun()
    with qcol3:
        if st.button(" Grande Desconto", width="stretch"):
            st.session_state['min_score'] = 6.0
            st.session_state['sort_by'] = "Desconto ↓"
            st.session_state['page'] = " Pesquisar"
            st.rerun()
    with qcol4:
        if st.button(" Ver no Mapa", width="stretch"):
            st.session_state['page'] = " Análise"
            st.session_state['analysis_page'] = " Mapa"
            st.rerun()
    with qcol5:
        if st.button(" Atualizar Dados", width="stretch"):
            st.rerun()

    #  TOP OPPORTUNITIES HERO CARDS 
    st.markdown("---")
    st.markdown("###  Top Oportunidades de Investimento")
    st.markdown(f"<p style='color:{TEXT_COLOR_MUTED_DARK};margin-top:-10px;'>Imóveis com maior lucro potencial estimado — clique para detalhes completos</p>", unsafe_allow_html=True)

    # Prepare top opportunities data
    try:
        opportunities = []
        for score in all_scores:
            l = score.listing
            if not l or not l.valuations:
                continue
            val = l.valuations[0]
            if not val.valor_justo or not l.preco_pedido:
                continue

            profit = val.valor_justo - l.preco_pedido
            profit_pct = (profit / l.preco_pedido) * 100 if l.preco_pedido > 0 else 0

            # Only show if profitable or high score
            if profit > 0 or score.score_total >= 7.0:
                opportunities.append({
                    "score": score,
                    "listing": l,
                    "valuation": val,
                    "profit": profit,
                    "profit_pct": profit_pct,
                    "price_m2": l.preco_por_m2 or (l.preco_pedido / l.area_util_m2 if l.area_util_m2 else 0),
                })

        # Sort by profit descending, then by score
        opportunities.sort(key=lambda x: (-x["profit"], -x["score"].score_total))
    except Exception as e:
        st.warning(f"Erro ao processar oportunidades: {str(e)}")
        opportunities = []

    # Display top 3 as cards (reduced from 6 for better 5-second rule compliance)
    if opportunities:
        for i in range(0, min(3, len(opportunities)), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(opportunities):
                    break
                opp = opportunities[idx]
                l = opp["listing"]
                score = opp["score"]
                profit = opp["profit"]
                profit_pct = opp["profit_pct"]
                color = profit_color(profit)

                with col:
                    # Card container
                    st.markdown(f"""
                    <div class="re-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div>{score_badge(score.score_total)}</div>
                            <div style="font-size:0.8em;color:{TEXT_COLOR_MUTED_DARK};">{score.classificacao or ""}</div>
                        </div>
                        <div style="font-weight:600;font-size:1.05em;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                            {(l.titulo or "Sem título")[:45]}{"..." if len(l.titulo or "") > 45 else ""}
                        </div>
                        <div style="font-size:0.85em;color:{TEXT_COLOR_MUTED_DARK};margin-bottom:8px;">
                            {l.freguesia or ""}{" — " if l.freguesia else ""}{l.tipologia or ""} | {l.area_util_m2:.0f}m²
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
                            <span style="font-size:1.3em;font-weight:700;color:{TEXT_COLOR_DARK};">
                                {l.preco_pedido:,.0f}€
                            </span>
                            <span style="font-size:0.85em;color:{TEXT_COLOR_MUTED_DARK};">
                                {opp['price_m2']:,.0f}€/m²
                            </span>
                        </div>
                        <div style="background:#0F172A;border:1px solid #334155;border-radius:8px;padding:8px 12px;margin-top:8px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-size:0.85em;color:{TEXT_COLOR_MUTED_DARK};">Valor Mercado:</span>
                                <span style="font-weight:600;">{opp['valuation'].valor_justo:,.0f}€</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">
                                <span style="font-size:0.85em;color:{TEXT_COLOR_MUTED_DARK};">Lucro Potencial:</span>
                                <span style="font-weight:700;color:{color};">
                                    +{profit:,.0f}€ ({profit_pct:+.1f}%)
                                </span>
                            </div>
                        </div>
                        <div style="margin-top:8px;font-size:0.8em;">
                            {f'<a href="{l.source_url}" target="_blank" style="color:{PRIMARY_COLOR};text-decoration:none;"> Ver anúncio original →</a>' if l.source_url else '<span style="color:{TEXT_COLOR_MUTED_DARK};"> Link não disponível</span>'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Sem oportunidades de investimento identificadas. Execute o pipeline para obter dados.")

    #  Detailed Opportunities Table 
    st.markdown("---")
    with st.expander(" Lista Detalhada de Oportunidades", expanded=True):
        st.markdown(f"<p style='color:{TEXT_COLOR_MUTED_DARK};margin-top:-10px;'>Todas as propriedades com score e valorização estimada — clica nas colunas para ordenar</p>", unsafe_allow_html=True)

        top = repo.get_top_scores(min_score=5.0, limit=100)
        if top:
            data = []
            for score in top:
                l = score.listing
                if not l:
                    continue

                discount_str = ""
                valor_str = ""
                lucro_bruto = 0
                lucro_str = ""
                lucro_pct = 0

                if l.valuations:
                    val = l.valuations[0]
                    if val.discount is not None:
                        pct = val.discount * 100
                        discount_str = pct

                if val.valor_justo and l.preco_pedido:
                    valor_str = val.valor_justo
                    lucro_bruto = val.valor_justo - l.preco_pedido
                    lucro_pct = (lucro_bruto / l.preco_pedido) * 100 if l.preco_pedido > 0 else 0
                    lucro_str = lucro_bruto

                is_watched = repo.is_in_watchlist(l.id)
                watch_indicator = "" if is_watched else ""

                data.append({
                    "": watch_indicator,
                    "": score.classificacao or "",
                    "Score": score.score_total,
                    "Lucro": lucro_str,
                    "Lucro_Val": lucro_bruto,
                    "Lucro_Pct": lucro_pct,
                    "Preço": l.preco_pedido if l.preco_pedido else None,
                    "V. Mercado": valor_str if valor_str else None,
                    "Desconto": discount_str if discount_str else None,
                    "€/m²": l.preco_por_m2 if l.preco_por_m2 else None,
                    "Portal": l.source_portal or "",
                    "Tipologia": l.tipologia or "",
                    "Quartos": l.quartos if l.quartos else None,
                    "Área": l.area_util_m2 if l.area_util_m2 else None,
                    "Freguesia": (l.freguesia or "")[:25],
                    "Concelho": (l.concelho or "")[:20],
                    "Estado": (l.estado or "").title() if l.estado else "",
                    "Cert.": l.cert_energetico or "",
                    "Título": (l.titulo or "")[:40] + "..." if l.titulo and len(l.titulo) > 40 else (l.titulo or ""),
                    " Link": l.source_url,
                    "_id": l.id,
                })

            df = pd.DataFrame(data)
            if not df.empty and "Score" in df.columns:
                df = df.sort_values(by="Lucro_Val", ascending=False)

            st.dataframe(
                df.drop(columns=["Lucro_Val", "Lucro_Pct", "_id"]),
                width='stretch',
                hide_index=True,
                column_config={
                    "": st.column_config.TextColumn("Watch", width="small"),
                    "": st.column_config.TextColumn("Class", width="small"),
                    " Link": st.column_config.LinkColumn("Link", display_text="Ver"),
                    "Score": st.column_config.NumberColumn("Score", format="%.1f"),
                    "Lucro": st.column_config.NumberColumn("Lucro Est. (€)", format="%.0f €"),
                    "Preço": st.column_config.NumberColumn("Preço", format="%.0f €"),
                    "V. Mercado": st.column_config.NumberColumn("V. Mercado", format="%.0f €"),
                    "Desconto": st.column_config.NumberColumn("Desconto", format="%.1f %%"),
                    "€/m²": st.column_config.NumberColumn("€/m²", format="%.0f €"),
                    "Área": st.column_config.NumberColumn("Área", format="%.0f m²"),
                    "Quartos": st.column_config.NumberColumn("Quartos", format="%d"),
                }
            )
        else:
            st.info("Sem oportunidades classificadas. Execute o pipeline primeiro.")

    #  Market Statistics 
    st.markdown("---")
    with st.expander(" Estatísticas de Mercado", expanded=False):
        if all_listings:
            prices = [l.preco_pedido for l in all_listings if l.preco_pedido and l.preco_pedido > 0]
            prices_m2 = [l.preco_por_m2 for l in all_listings if l.preco_por_m2 and l.preco_por_m2 > 0]

            if prices and prices_m2:
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    st.metric(" Preço Mediano", f"{statistics.median(prices):,.0f}€".replace(",", "."))
                with col_b:
                    st.metric(" €/m² Mediano", f"{statistics.median(prices_m2):,.0f}€".replace(",", "."))
                with col_c:
                    areas = [l.area_util_m2 for l in all_listings if l.area_util_m2 and l.area_util_m2 > 0]
                    if areas:
                        st.metric(" Área Mediana", f"{statistics.median(areas):.0f}m²")
                with col_d:
                    freguesias = set(l.freguesia for l in all_listings if l.freguesia)
                    st.metric(" Freguesias", len(freguesias))

    #  Classification Distribution 
    st.markdown("---")
    with st.expander(" Distribuição por Classificação", expanded=False):
        col_chart, col_table = st.columns([1, 1])

        with col_chart:
            if all_scores:
                class_data = {}
                for s in all_scores:
                    c = s.classificacao or "Sem classificação"
                    class_data[c] = class_data.get(c, 0) + 1

                present_classifications = sorted(class_data.keys())

                class_colors = {
                    "Imperdível": "#dc2626", "Excelente": "#ea580c",
                    "Bom": "#16a34a", "Aceitável": "#6b7280",
                    "Abaixo da média": "#ca8a04", "Não recomendado": "#991b1b"
                }
                filtered_class_colors = {k: v for k, v in class_colors.items() if k in class_data}

                df_class = pd.DataFrame([
                    {"Classificação": c, "Total": class_data.get(c, 0)}
                    for c in present_classifications
                ])

                if not df_class.empty:
                    try:
                        import plotly.express as px
                        fig = px.bar(df_class, x="Classificação", y="Total",
                                     color="Classificação",
                                     color_discrete_map=filtered_class_colors)
                        fig.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Erro ao renderizar gráfico: {e}")
                        st.dataframe(df_class, hide_index=True)

        with col_table:
            if all_scores:
                scores_list = [s.score_total for s in all_scores]
                st.write(f"**Média:** {statistics.mean(scores_list):.1f}")
                st.write(f"**Mediana:** {statistics.median(scores_list):.1f}")
                st.write(f"**Máximo:** {max(scores_list):.1f}")
                st.write(f"**Mínimo:** {min(scores_list):.1f}")
                if len(scores_list) > 1:
                    st.write(f"**Desvio padrão:** {statistics.stdev(scores_list):.2f}")

    #  Pipeline Health Mini-Status 
    st.markdown("---")
    with st.expander(" Estado do Pipeline", expanded=False):
        from realestate_engine.monitoring.health_checks import HealthCheck
        hc = HealthCheck()
        checks = hc.get_all_checks()

        overall = checks.get("overall", "unknown")
        emoji = "" if overall == "healthy" else "" if overall in ("degraded", "warning") else ""
        st.markdown(f"**Sistema:** {emoji} {overall.upper()}")

        # Show details for non-healthy components
        for label, key in [(" Base de Dados", "database"), (" Scraping", "scraping"),
                           ("⏰ Scheduler", "scheduler"), (" APIs Externas", "external_apis")]:
            check = checks.get(key, {})
            status = check.get("status", "unknown")
            if status != "healthy":
                note = check.get("note", check.get("error", ""))
                fix = check.get("fix", "")
                e = "" if status in ("warning", "degraded") else ""
                st.markdown(f"{e} **{label}:** {note}")
                if fix:
                    st.caption(f" {fix}")
