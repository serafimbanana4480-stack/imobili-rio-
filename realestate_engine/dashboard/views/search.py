"""Search and filter page for dashboard.

Enhanced with:
- Advanced multi-filter search
- Side-by-side property comparison
- Score breakdown visualization
- Valuation details per listing
- Direct link to original listing
"""
import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.database.repository import DatabaseRepository


# Porto and Grande Porto freguesias for dropdown
PORTO_FREGUESIAS = [
    "", "Foz do Douro", "Nevogilde", "Aldoar", "Massarelos", "Lordelo do Ouro",
    "Cedofeita", "Santo Ildefonso", "Sé", "Miragaia", "São Nicolau", "Vitória",
    "Bonfim", "Paranhos", "Ramalde", "Campanha",
    "Matosinhos", "Leça da Palmeira", "Senhora da Hora",
    "Mafamude", "Canidelo", "Santa Marinha",
]

TIPOLOGIAS = ["Todas", "T0", "T1", "T2", "T3", "T4", "T5+"]
ESTADOS = ["Todos", "Novo", "Renovado", "Bom", "Usado", "Para Recuperar"]


def render_search():
    """Render search and filter page."""
    st.title("🔍 Pesquisa & Filtros")
    st.markdown("*Encontre oportunidades específicas no mercado do Porto*")

    repo = DatabaseRepository()

    # ── Quick Filters ─────────────────────────────────────────────────────
    st.markdown("### 🎯 Filtros Rápidos")
    
    # Preset quick filters
    col_preset1, col_preset2, col_preset3, col_preset4 = st.columns(4)
    
    with col_preset1:
        if st.button("💰 Oportunidades", use_container_width=True):
            st.session_state['min_score'] = 7.0
            st.session_state['min_price'] = 0
            st.session_state['max_price'] = 500000
            st.rerun()
    
    with col_preset2:
        if st.button("🏠 T2-T3", use_container_width=True):
            st.session_state['tipologia'] = "T2"
            st.rerun()
    
    with col_preset3:
        if st.button("📍 Centro", use_container_width=True):
            st.session_state['freguesia'] = "União de Freguesias do Centro"
            st.rerun()
    
    with col_preset4:
        if st.button("🔄 Limpar Filtros", use_container_width=True):
            for key in ['min_price', 'max_price', 'min_area', 'max_area', 'min_score', 'tipologia', 'freguesia', 'estado']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # ── Advanced Filters ───────────────────────────────────────────────────
    with st.expander("⚙️ Filtros Avançados", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_price = st.number_input("Preço Mín (€)", min_value=0, value=st.session_state.get('min_price', 0), step=10000)
            max_price = st.number_input("Preço Máx (€)", min_value=0, value=st.session_state.get('max_price', 1_000_000), step=25000)

        with col2:
            min_area = st.number_input("Área Mín (m²)", min_value=0, value=st.session_state.get('min_area', 0), step=10)
            max_area = st.number_input("Área Máx (m²)", min_value=0, value=st.session_state.get('max_area', 500), step=10)

        with col3:
            min_score = st.slider("Score Mínimo", 0.0, 10.0, st.session_state.get('min_score', 5.0), 0.5)
            tipologia = st.selectbox("Tipologia", TIPOLOGIAS, index=TIPOLOGIAS.index(st.session_state.get('tipologia', "Todas")) if st.session_state.get('tipologia', "Todas") in TIPOLOGIAS else 0)

        with col4:
            freguesia = st.selectbox("Freguesia", PORTO_FREGUESIAS, index=PORTO_FREGUESIAS.index(st.session_state.get('freguesia', "")) if st.session_state.get('freguesia', "") in PORTO_FREGUESIAS else 0)
            estado = st.selectbox("Estado", ESTADOS, index=ESTADOS.index(st.session_state.get('estado', "Todos")) if st.session_state.get('estado', "Todos") in ESTADOS else 0)

    col_sort, col_order = st.columns(2)
    with col_sort:
        sort_by = st.selectbox("Ordenar por", ["Score", "Preço ↑", "Preço ↓", "€/m² ↑", "€/m² ↓", "Área ↓"], index=["Score", "Preço ↑", "Preço ↓", "€/m² ↑", "€/m² ↓", "Área ↓"].index(st.session_state.get('sort_by', "Score")) if st.session_state.get('sort_by', "Score") in ["Score", "Preço ↑", "Preço ↓", "€/m² ↑", "€/m² ↓", "Área ↓"] else 0)
    with col_order:
        max_results = st.selectbox("Resultados", [25, 50, 100, 200], index=[25, 50, 100, 200].index(st.session_state.get('max_results', 50)) if st.session_state.get('max_results', 50) in [25, 50, 100, 200] else 1)
    
    # Save filter presets
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Guardar Filtros")
    preset_name = st.sidebar.text_input("Nome do Preset", key="preset_name")
    
    # Load existing presets
    if 'filter_presets' not in st.session_state:
        st.session_state.filter_presets = {}
    
    if st.sidebar.button("💾 Guardar Filtros Atuais", key="save_preset"):
        if preset_name:
            st.session_state.filter_presets[preset_name] = {
                'min_price': min_price,
                'max_price': max_price,
                'min_area': min_area,
                'max_area': max_area,
                'min_score': min_score,
                'tipologia': tipologia,
                'freguesia': freguesia,
                'estado': estado,
                'sort_by': sort_by,
                'max_results': max_results,
            }
            st.sidebar.success(f"Preset '{preset_name}' guardado!")
        else:
            st.sidebar.warning("Digite um nome para o preset.")
    
    # Load preset
    if st.session_state.filter_presets:
        st.sidebar.markdown("**Presets Guardados:**")
        for preset in st.session_state.filter_presets.keys():
            if st.sidebar.button(f"📂 {preset}", key=f"load_{preset}"):
                preset_data = st.session_state.filter_presets[preset]
                st.session_state['min_price'] = preset_data['min_price']
                st.session_state['max_price'] = preset_data['max_price']
                st.session_state['min_area'] = preset_data['min_area']
                st.session_state['max_area'] = preset_data['max_area']
                st.session_state['min_score'] = preset_data['min_score']
                st.session_state['tipologia'] = preset_data['tipologia']
                st.session_state['freguesia'] = preset_data['freguesia']
                st.session_state['estado'] = preset_data['estado']
                st.session_state['sort_by'] = preset_data['sort_by']
                st.session_state['max_results'] = preset_data['max_results']
                st.sidebar.success(f"Preset '{preset}' carregado!")
                st.rerun()

    # ── Search ──────────────────────────────────────────────────────────
    # Auto-search if user arrived from a chart drill-down
    auto_search = st.session_state.pop("auto_search", False)
    search_clicked = st.button("🔍 Pesquisar", type="primary", use_container_width=True)
    if search_clicked or auto_search:
        if auto_search:
            st.info("🎯 Filtros aplicados automaticamente a partir do gráfico clicado")
        listings = repo.get_clean_listings(limit=5000)
        results = []

        for l in listings:
            # Price filter
            if l.preco_pedido:
                if l.preco_pedido < min_price:
                    continue
                if max_price > 0 and l.preco_pedido > max_price:
                    continue

            # Area filter
            if l.area_util_m2:
                if l.area_util_m2 < min_area:
                    continue
                if max_area > 0 and l.area_util_m2 > max_area:
                    continue

            # Freguesia filter
            if freguesia and freguesia.lower() not in (l.freguesia or "").lower():
                continue

            # Estado filter
            if estado != "Todos":
                l_estado = (l.estado or "").lower()
                filter_estado = estado.lower().replace(" ", "_")
                if filter_estado not in l_estado:
                    continue

            # Tipologia filter
            if tipologia != "Todas":
                l_tipo = (l.tipologia or "").upper()
                if tipologia == "T5+":
                    if not any(l_tipo.startswith(f"T{i}") for i in range(5, 10)):
                        continue
                elif tipologia not in l_tipo:
                    continue

            # Get score
            score = repo.get_score_by_listing(l.id)
            score_total = score.score_total if score else 0

            if score_total < min_score:
                continue

            # Get valuation
            val = l.valuations[0] if l.valuations else None
            pct = None
            discount_str = ""
            valor_justo = ""
            confianca = ""
            if val:
                if val.discount is not None:
                    pct = val.discount * 100
                    discount_str = f"{pct:+.0f}%"
                if val.valor_justo:
                    valor_justo = f"{val.valor_justo:,.0f}€".replace(",", ".")
                if val.confianca is not None:
                    confianca = f"{val.confianca:.0%}"

            # Data source attribution
            scrape_date = l.scrape_timestamp
            try:
                days_ago = (pd.Timestamp.now() - pd.Timestamp(scrape_date)).days if scrape_date else None
            except Exception:
                days_ago = None
            freshness = f"{days_ago}d" if days_ago is not None else "N/A"
            
            results.append({
                "id": l.id,
                "🏆": score.classificacao if score else "",
                "Score": score_total,
                "Portal": l.source_portal,
                "📅": freshness,
                "Título": (l.titulo or "")[:45],
                "Preço": l.preco_pedido,
                "Área": l.area_util_m2,
                "€/m²": l.preco_por_m2 or 0,
                "Quartos": l.quartos or 0,
                "Desconto": pct if val and val.discount is not None else None,
                "V. Justo": val.valor_justo if val and val.valor_justo else None,
                "Confiança": confianca,
                "Freguesia": l.freguesia or "",
                "Estado": (l.estado or "").title(),
                "Cert.": l.cert_energetico or "",
                "🔗": l.source_url,
            })

        # Sort
        if sort_by == "Score":
            results.sort(key=lambda x: x["Score"], reverse=True)
        elif sort_by == "Preço ↑":
            results.sort(key=lambda x: x.get("Preço") or 0)
        elif sort_by == "Preço ↓":
            results.sort(key=lambda x: x.get("Preço") or 0, reverse=True)
        elif sort_by == "€/m² ↑":
            results.sort(key=lambda x: x.get("€/m²") or 0)
        elif sort_by == "€/m² ↓":
            results.sort(key=lambda x: x.get("€/m²") or 0, reverse=True)
        elif sort_by == "Área ↓":
            results.sort(key=lambda x: x.get("Área") or 0, reverse=True)

        results = results[:max_results]

        st.write(f"**{len(results)} resultados encontrados**")

        if results:
            # Display table (hide internal columns)
            display_cols = [
                "🏆", "Score", "Portal", "📅", "Título", "Preço", "Área",
                "€/m²", "Quartos", "Desconto", "V. Justo", "Freguesia", "Estado", "Cert.", "🔗"
            ]
            df = pd.DataFrame(results)[display_cols]
            df.columns = [
                "🏆", "Score", "Portal", "Idade", "Título", "Preço", "Área",
                "€/m²", "Q.", "Desconto", "V. Justo", "Freguesia", "Estado", "Cert.", "🔗"
            ]

            st.dataframe(
                df, use_container_width=True, hide_index=True,
                column_config={
                    "Idade": st.column_config.TextColumn("Idade", width="small", help="Dias desde o scrape"),
                    "🔗": st.column_config.LinkColumn("Link", display_text="Ver"),
                    "Score": st.column_config.NumberColumn("Score", format="%.1f"),
                    "Preço": st.column_config.NumberColumn("Preço", format="%.0f €"),
                    "Área": st.column_config.NumberColumn("Área", format="%.0f m²"),
                    "€/m²": st.column_config.NumberColumn("€/m²", format="%.0f €/m²"),
                    "Desconto": st.column_config.NumberColumn("Desconto", format="%.1f %%"),
                    "V. Justo": st.column_config.NumberColumn("V. Justo", format="%.0f €"),
                }
            )

            titles = [f"{r['Título']} - {r['Preço']:,.0f}€" for r in results[:20]]
            selected = st.multiselect("Escolha imóveis:", titles, max_selections=3)

            if selected:
                comp_cols = st.columns(len(selected))
                for i, sel in enumerate(selected):
                    idx = titles.index(sel)
                    r = results[idx]
                    with comp_cols[i]:
                        st.markdown(f"**{r['Título']}**")
                        st.write(f"💵 {r['Preço']:,.0f}€".replace(",", "."))
                        st.write(f"📐 {r['Área']:.0f}m² ({r['€/m²']:,.0f}€/m²)".replace(",", "."))
                        st.write(f"🛏️ {r['Quartos']} quartos")
                        st.write(f"📍 {r['Freguesia']}")
                        st.write(f"🔧 {r['Estado']} | Cert: {r['Cert.']}")
                        st.write(f"📊 Score: **{r['Score']:.1f}** ({r['🏆']})")
                        st.write(f"💰 Desconto: {r['Desconto']}")
                        st.write(f"📈 V. Justo: {r['V. Justo']}")
                        st.write(f"🎯 Confiança: {r['Confiança']}")
                        if r["🔗"]:
                            st.link_button("🔗 Ver anúncio", r["🔗"])
                        else:
                            st.caption("🔗 Link não disponível")
        else:
            st.info("Nenhum anúncio corresponde aos critérios selecionados.")
