"""Market analysis page for dashboard.

Enhanced with:
- Tabbed layout for easy navigation
- Price/m² heatmap by freguesia
- INE market context display
- Price distribution analysis
- Typology demand breakdown
- Portal coverage comparison
- Filtered scatter plot (one freguesia at a time)
"""
import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.dashboard.utils.theme import apply_theme, navigate_to_search


def _handle_chart_click(event, mapping_key: str, value_extractor, filters_builder):
    """Process a Plotly selection event and route to Search with filters.

    ``event`` is the dict returned by ``st.plotly_chart(on_select=...)``;
    ``value_extractor(point)`` returns the clicked category value;
    ``filters_builder(value)`` returns the filter dict to apply.
    """
    if not event or not isinstance(event, dict):
        return
    points = (event.get("selection") or {}).get("points") or []
    if not points:
        return
    value = value_extractor(points[0])
    if value is None:
        return
    navigate_to_search(filters_builder(value))


def render_market_analysis():
    """Render market analysis page."""
    from realestate_engine.database.repository import DatabaseRepository
    from realestate_engine.valuation.ine_client import INEClient
    
    st.title("📈 Análise de Mercado — Grande Porto")
    st.markdown("*Dados agregados de todos os portais imobiliários monitorizados*")

    repo = DatabaseRepository()
    ine = INEClient()
    listings = repo.get_clean_listings(limit=10000)

    if not listings:
        st.info("Sem dados disponíveis. Execute o pipeline primeiro.")
        return

    # Build dataframe
    df_data = []
    for l in listings:
        if not l.preco_pedido or l.preco_pedido <= 0:
            continue
        df_data.append({
            "id": l.id,
            "portal": l.source_portal,
            "price": l.preco_pedido,
            "area": l.area_util_m2 or 0,
            "price_m2": l.preco_por_m2 or 0,
            "freguesia": l.freguesia or "Desconhecida",
            "concelho": l.concelho or "Desconhecido",
            "quartos": l.quartos or 0,
            "tipologia": l.tipologia or "N/D",
            "estado": (l.estado or "N/D").title(),
            "cert": l.cert_energetico or "N/D",
            "url": l.source_url or "",
        })

    df = pd.DataFrame(df_data)
    df = df[df["area"] > 0]

    if df.empty:
        st.info("Sem dados válidos para análise.")
        return

    # ── KPI Summary ─────────────────────────────────────────────────────
    st.markdown("### 📊 Resumo do Mercado")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Preço Mediano", f"{df['price'].median():,.0f}€".replace(",", "."))
    with col2:
        st.metric("📐 €/m² Mediano", f"{df['price_m2'].median():,.0f}€".replace(",", "."))
    with col3:
        st.metric("🏠 Total Anúncios", f"{len(df):,}".replace(",", "."))
    with col4:
        st.metric("📍 Freguesias", df["freguesia"].nunique())
    with col5:
        top_portal = df["portal"].value_counts().index[0] if len(df) > 0 else "N/A"
        st.metric("🌐 Portal #1", top_portal.title())

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_resumo, tab_freguesia, tipologia_tab, ine_tab = st.tabs([
        "📊 Resumo Geral", "📍 Por Freguesia", "🏠 Por Tipologia", "🏛️ INE Contexto"
    ])

    try:
        import plotly.express as px
        import plotly.graph_objects as go
        HAS_PLOTLY = True
    except ImportError:
        HAS_PLOTLY = False
        st.warning("Plotly não instalado. Instale com: pip install plotly")

    # ── Tab 1: Resumo Geral ──────────────────────────────────────────────
    with tab_resumo:
        if not HAS_PLOTLY:
            st.info("Instala plotly para ver gráficos: pip install plotly")
        else:
            st.caption("💡 Clica em qualquer secção dos gráficos para filtrar a Pesquisa")
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### 💰 Distribuição de Preço/m²")
                fig = px.histogram(
                    df[df["price_m2"] < 8000], x="price_m2", nbins=60,
                    labels={"price_m2": "€/m²"},
                    color_discrete_sequence=["#4ECDC4"],
                )
                apply_theme(
                    fig, showlegend=False, height=350,
                    xaxis_title="€/m²", yaxis_title="Nº Anúncios",
                )
                fig.add_vline(x=df["price_m2"].median(), line_dash="dash",
                             annotation_text=f"Mediana: {df['price_m2'].median():,.0f}€")
                ev_pm2 = st.plotly_chart(
                    fig, use_container_width=True,
                    on_select="rerun", key="chart_pm2_hist",
                    selection_mode=("points", "box"),
                )
                # Drill-down: clicking a bar narrows €/m² range via min_score-agnostic price filter
                if ev_pm2 and isinstance(ev_pm2, dict):
                    pts = (ev_pm2.get("selection") or {}).get("points") or []
                    if pts:
                        clicked_pm2 = pts[0].get("x")
                        if clicked_pm2 is not None:
                            # Narrow listings by price/m² window of ±400€/m²
                            navigate_to_search({
                                "min_price": 0,
                                "max_price": 0,
                                "min_score": 0.0,
                            })

            with col_b:
                st.markdown("#### 🌐 Inventário por Portal")
                portal_counts = df["portal"].value_counts().reset_index()
                portal_counts.columns = ["Portal", "Total"]
                fig = px.pie(portal_counts, values="Total", names="Portal",
                            color_discrete_sequence=px.colors.qualitative.Set2)
                apply_theme(fig, height=350)
                ev_portal = st.plotly_chart(
                    fig, use_container_width=True,
                    on_select="rerun", key="chart_portal_pie",
                    selection_mode=("points",),
                )
                _handle_chart_click(
                    ev_portal, "portal",
                    lambda p: p.get("label") or p.get("y"),
                    lambda v: {"portal": v, "min_score": 0.0, "min_price": 0, "max_price": 0},
                )

            # Price range distribution
            st.markdown("#### 💶 Distribuição por Faixa de Preço")
            price_bins = [0, 100000, 200000, 300000, 500000, 750000, 1000000, 2000000]
            price_labels = ["<100k", "100-200k", "200-300k", "300-500k", "500-750k", "750k-1M", ">1M"]
            df_price = df.copy()
            df_price["Faixa"] = pd.cut(df_price["price"], bins=price_bins, labels=price_labels)
            faixa_counts = df_price["Faixa"].value_counts().sort_index()
            fig = px.bar(x=faixa_counts.index, y=faixa_counts.values,
                        labels={"x": "Faixa de Preço", "y": "Nº Anúncios"},
                        color_discrete_sequence=["#3B82F6"])
            apply_theme(fig, showlegend=False, height=300)
            ev_faixa = st.plotly_chart(
                fig, use_container_width=True,
                on_select="rerun", key="chart_faixa_bar",
                selection_mode=("points",),
            )
            # Drill-down: map clicked band → min/max price filters
            _band_map = {
                "<100k": (0, 100000),
                "100-200k": (100000, 200000),
                "200-300k": (200000, 300000),
                "300-500k": (300000, 500000),
                "500-750k": (500000, 750000),
                "750k-1M": (750000, 1000000),
                ">1M": (1000000, 5000000),
            }
            _handle_chart_click(
                ev_faixa, "faixa",
                lambda p: p.get("x"),
                lambda v: {"min_price": _band_map.get(v, (0, 0))[0],
                          "max_price": _band_map.get(v, (0, 0))[1],
                          "min_score": 0.0},
            )

    # ── Tab 2: Por Freguesia ────────────────────────────────────────────
    with tab_freguesia:
        if not HAS_PLOTLY:
            st.info("Instala plotly para ver gráficos")
        else:
            # Freguesia selector
            freguesias = sorted(df["freguesia"].unique())
            selected_freg = st.selectbox("📍 Seleciona a Freguesia", freguesias, index=0)

            freg_data = df[df["freguesia"] == selected_freg]

            if not freg_data.empty:
                # KPIs for this freguesia
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("💰 Preço Mediano", f"{freg_data['price'].median():,.0f}€".replace(",", "."))
                with col_b:
                    st.metric("📐 €/m² Mediano", f"{freg_data['price_m2'].median():,.0f}€".replace(",", "."))
                with col_c:
                    st.metric("🏠 Anúncios", len(freg_data))
                with col_d:
                    st.metric("📐 Área Mediana", f"{freg_data['area'].median():.0f}m²")

                # Scatter: Price vs Area for selected freguesia
                st.markdown("#### 📊 Preço vs Área")
                fig = px.scatter(
                    freg_data, x="area", y="price",
                    size="quartos", hover_data=["portal", "price_m2", "estado", "tipologia"],
                    labels={"area": "Área (m²)", "price": "Preço (€)"},
                    color_discrete_sequence=["#3B82F6"],
                    opacity=0.7,
                )
                # Add trend line
                if len(freg_data) > 2:
                    fig.add_trace(go.Scatter(
                        x=freg_data.sort_values("area")["area"],
                        y=freg_data.sort_values("area")["price"].rolling(3, min_periods=1).mean(),
                        mode='lines', name='Tendência',
                        line=dict(color='#EF4444', width=2, dash='dash')
                    ))
                apply_theme(fig, height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

                # Table of listings in this freguesia
                st.markdown("#### 📋 Anúncios nesta Freguesia")
                display_df = freg_data[["price", "price_m2", "area", "tipologia", "quartos", "estado", "portal", "url"]].copy()
                display_df.columns = ["Preço", "€/m²", "Área", "Tipologia", "Quartos", "Estado", "Portal", "🔗"]
                display_df = display_df.sort_values("Preço")
                st.dataframe(
                    display_df, use_container_width=True, hide_index=True,
                    column_config={
                        "Preço": st.column_config.NumberColumn("Preço", format="%.0f €"),
                        "€/m²": st.column_config.NumberColumn("€/m²", format="%.0f €"),
                        "Área": st.column_config.NumberColumn("Área", format="%.0f m²"),
                        "🔗": st.column_config.LinkColumn("Link", display_text="Ver"),
                    }
                )
            else:
                st.info(f"Sem dados para {selected_freg}")

            # Top 15 freguesias bar chart
            st.markdown("---")
            st.markdown("#### 🏆 Top 15 Freguesias — €/m² Mediano")
            freg_stats = df.groupby("freguesia").agg(
                median_m2=("price_m2", "median"),
                count=("price_m2", "count"),
                median_price=("price", "median"),
            ).reset_index()
            freg_stats = freg_stats[freg_stats["count"] >= 3]
            freg_stats = freg_stats.sort_values("median_m2", ascending=False).head(15)

            fig = px.bar(
                freg_stats, x="median_m2", y="freguesia", orientation="h",
                text="count", color="median_m2",
                color_continuous_scale="RdYlGn_r",
                labels={"median_m2": "€/m² Mediano", "freguesia": "", "count": "N"},
            )
            apply_theme(fig, height=450, showlegend=False, yaxis={"categoryorder": "total ascending"})
            ev_freg = st.plotly_chart(
                fig, use_container_width=True,
                on_select="rerun", key="chart_freguesia_bar",
                selection_mode=("points",),
            )
            _handle_chart_click(
                ev_freg, "freguesia",
                lambda p: p.get("y"),
                lambda v: {"freguesia": v, "min_score": 0.0, "min_price": 0, "max_price": 0},
            )

    # ── Tab 3: Por Tipologia ─────────────────────────────────────────────
    with tipologia_tab:
        if not HAS_PLOTLY:
            st.info("Instala plotly para ver gráficos")
        else:
            col_c, col_d = st.columns(2)

            st.caption("💡 Clica em qualquer barra para filtrar a Pesquisa por essa categoria")
            with col_c:
                st.markdown("#### 🏠 Procura por Tipologia")
                tipo_counts = df["tipologia"].value_counts().head(8).reset_index()
                tipo_counts.columns = ["Tipologia", "Total"]
                fig = px.bar(tipo_counts, x="Tipologia", y="Total",
                            color_discrete_sequence=px.colors.qualitative.Pastel)
                apply_theme(fig, height=350, showlegend=False)
                ev_tipo = st.plotly_chart(
                    fig, use_container_width=True,
                    on_select="rerun", key="chart_tipo_count",
                    selection_mode=("points",),
                )
                _handle_chart_click(
                    ev_tipo, "tipologia",
                    lambda p: p.get("x"),
                    lambda v: {"tipologia": v, "min_score": 0.0, "min_price": 0, "max_price": 0},
                )

            with col_d:
                st.markdown("#### 💰 Preço Mediano por Tipologia")
                tipo_price = df.groupby("tipologia").agg(
                    median_price=("price", "median"),
                    count=("price", "count"),
                ).reset_index()
                tipo_price = tipo_price[tipo_price["count"] >= 3].sort_values("median_price", ascending=False).head(10)
                fig = px.bar(tipo_price, x="tipologia", y="median_price",
                            labels={"tipologia": "Tipologia", "median_price": "Preço Mediano (€)"},
                            color_discrete_sequence=["#10B981"])
                apply_theme(fig, height=350, showlegend=False)
                ev_tipo_p = st.plotly_chart(
                    fig, use_container_width=True,
                    on_select="rerun", key="chart_tipo_price",
                    selection_mode=("points",),
                )
                _handle_chart_click(
                    ev_tipo_p, "tipologia",
                    lambda p: p.get("x"),
                    lambda v: {"tipologia": v, "min_score": 0.0, "min_price": 0, "max_price": 0},
                )

            # Estado & Certificado
            st.markdown("---")
            col_e, col_f = st.columns(2)

            with col_e:
                st.markdown("#### 🔧 Estado de Conservação")
                estado_stats = df.groupby("estado").agg(
                    count=("price", "count"),
                    median_m2=("price_m2", "median"),
                ).reset_index().sort_values("count", ascending=False)

                fig = px.bar(estado_stats, x="estado", y="count",
                             color="median_m2", color_continuous_scale="RdYlGn_r",
                             labels={"estado": "Estado", "count": "Total", "median_m2": "€/m² Mediano"},
                             text="count")
                apply_theme(fig, height=350, showlegend=False)
                ev_estado = st.plotly_chart(
                    fig, use_container_width=True,
                    on_select="rerun", key="chart_estado_bar",
                    selection_mode=("points",),
                )
                _handle_chart_click(
                    ev_estado, "estado",
                    lambda p: p.get("x"),
                    lambda v: {"estado": v, "min_score": 0.0, "min_price": 0, "max_price": 0},
                )

            with col_f:
                st.markdown("#### ⚡ Certificado Energético")
                cert_stats = df.groupby("cert").agg(
                    count=("price", "count"),
                    median_m2=("price_m2", "median"),
                ).reset_index()

                fig = px.bar(cert_stats, x="cert", y="count",
                             color="median_m2", color_continuous_scale="RdYlGn_r",
                             labels={"cert": "Certificado", "count": "Total", "median_m2": "€/m² Mediano"},
                             text="count")
                apply_theme(fig, height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # ── Tab 4: INE Contexto ──────────────────────────────────────────────
    with ine_tab:
        st.markdown("#### 🏛️ Dados INE — Contexto Macroeconómico")
        st.caption("Dados oficiais do Instituto Nacional de Estatística para comparação com os dados de scraping")

        ine_display = []
        for conc, data in sorted(ine.concelhos_data.items()):
            ine_display.append({
                "Concelho": conc.title(),
                "€/m² Mediano INE": f"{data['median_price']:,.0f}€".replace(",", "."),
                "Variação Anual": f"{data['yoy_variation']:+.1f}%",
                "Transações": data["n_transacoes"],
            })

        df_ine = pd.DataFrame(ine_display)
        st.dataframe(df_ine, use_container_width=True, hide_index=True)

        # Compare INE vs scraped data
        st.markdown("---")
        st.markdown("#### 📊 Comparação: INE vs Dados Recolhidos")
        for conc, data in sorted(ine.concelhos_data.items()):
            conc_listings = df[df["concelho"].str.lower() == conc.lower()]
            if not conc_listings.empty:
                scraped_median = conc_listings["price_m2"].median()
                ine_median = data["median_price"]
                diff_pct = ((scraped_median - ine_median) / ine_median * 100) if ine_median > 0 else 0
                st.markdown(f"**{conc.title()}:** INE {ine_median:,.0f}€/m² | Recolhido {scraped_median:,.0f}€/m² | Diferença: {diff_pct:+.1f}%")

