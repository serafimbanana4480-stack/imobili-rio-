"""Map view page for dashboard.

Interactive map with property pins for geographic analysis.
"""
import streamlit as st
import pandas as pd
import pydeck as pdk
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.database.repository import DatabaseRepository


def render_map_view():
    """Render interactive map view with property pins."""
    st.title(" Mapa de Propriedades")
    st.markdown("*Visualização geográfica de todas as propriedades no mercado*")

    repo = DatabaseRepository()

    # Get listings with coordinates (real data only)
    listings = repo.get_clean_listings(limit=5000)
    
    # Filter listings with valid coordinates
    valid_listings = [l for l in listings if l.lat and l.lon and l.preco_pedido]

    if not valid_listings:
        st.info("Sem propriedades com coordenadas válidas. Execute o pipeline primeiro.")
        return

    # Build dataframe for map
    map_data = []
    for l in valid_listings:
        score = repo.get_score_by_listing(l.id)
        
        # Determine marker color based on score
        if score and score.score_total >= 8.0:
            marker_color = "red"  # Imperdível
        elif score and score.score_total >= 7.0:
            marker_color = "orange"  # Excelente
        elif score and score.score_total >= 5.0:
            marker_color = "blue"  # Bom
        else:
            marker_color = "gray"  # Abaixo da média

        map_data.append({
            "lat": l.lat,
            "lon": l.lon,
            "name": f"{l.titulo or 'Sem título'}"[:50],
            "price": f"{l.preco_pedido:,.0f}€".replace(",", "."),
            "price_m2": f"{l.preco_por_m2:,.0f}€".replace(",", ".") if l.preco_por_m2 else "N/A",
            "area": f"{l.area_util_m2:.0f}m²" if l.area_util_m2 else "N/A",
            "freguesia": l.freguesia or "N/A",
            "score": f"{score.score_total:.1f}" if score else "N/A",
            "portal": l.source_portal,
            "url": l.source_url or "",
            "color": [255, 0, 0, 180] if marker_color == "red" else [255, 165, 0, 180] if marker_color == "orange" else [59, 130, 246, 180] if marker_color == "blue" else [107, 114, 128, 180],
            "marker_color": marker_color
        })

    df = pd.DataFrame(map_data)

    if df.empty:
        st.info("Sem dados suficientes para desenhar o mapa.")
        return

    # Filter options
    st.sidebar.subheader(" Filtros do Mapa")
    
    min_price = st.sidebar.number_input("Preço Mín (€)", min_value=0, value=0, step=10000)
    max_price = st.sidebar.number_input("Preço Máx (€)", min_value=0, value=2_000_000, step=50000)
    
    score_filter = st.sidebar.selectbox(
        "Filtrar por Score",
        ["Todos", "Imperdível (8+)", "Excelente (7+)", "Bom (5+)", "Abaixo da média"],
        index=0
    )

    # Apply filters
    if min_price > 0:
        df = df[df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '').astype(float) >= min_price]
    if max_price > 0:
        df = df[df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '').astype(float) <= max_price]
    
    if score_filter == "Imperdível (8+)":
        df = df[df['score'] != "N/A"]
        df = df[df['score'].astype(float) >= 8.0]
    elif score_filter == "Excelente (7+)":
        df = df[df['score'] != "N/A"]
        df = df[df['score'].astype(float) >= 7.0]
    elif score_filter == "Bom (5+)":
        df = df[df['score'] != "N/A"]
        df = df[df['score'].astype(float) >= 5.0]
    elif score_filter == "Abaixo da média":
        df = df[df['score'] != "N/A"]
        df = df[df['score'].astype(float) < 5.0]

    if df.empty:
        st.warning("Nenhuma propriedade corresponde aos filtros selecionados.")
        return

    # Display map using pydeck with tooltips and clear color coding
    st.subheader(f" {len(df)} Propriedades no Mapa")
    st.caption(f"Filtrado por: Preço {min_price:,.0f}€ - {max_price:,.0f}€ | Score: {score_filter}")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=120,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=11,
        pitch=0,
    )

    tooltip = {
        "html": "<b>{name}</b><br/>Preço: {price}<br/>€/m²: {price_m2}<br/>Score: {score}<br/>Freguesia: {freguesia}<br/>Portal: {portal}",
        "style": {"backgroundColor": "white", "color": "black"},
    }

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

    # Legend
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(" **Imperdível (8+)**")
    with col2:
        st.markdown(" **Excelente (7+)**")
    with col3:
        st.markdown(" **Bom (5+)**")
    with col4:
        st.markdown(" **Abaixo da média**")

    # Statistics
    st.markdown("---")
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        st.metric("Total", f"{len(df)}")
    with col_b:
        avg_price = df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '').astype(float).mean()
        st.metric("Preço Médio", f"{avg_price:,.0f}€".replace(",", "."))
    with col_c:
        avg_m2 = df[df['price_m2'] != "N/A"]['price_m2'].str.replace('€', '').str.replace('.', '').str.replace(',', '').astype(float).mean()
        st.metric("€/m² Médio", f"{avg_m2:,.0f}€".replace(",", ".") if pd.notna(avg_m2) else "N/A")
    with col_d:
        unique_freg = df['freguesia'].nunique()
        st.metric("Freguesias", unique_freg)

    # Property details below map
    st.markdown("---")
    st.subheader(" Lista de Propriedades")

    selection_options = df.index.tolist()
    selected_idx = st.selectbox(
        "Escolhe uma propriedade para ver detalhes e abrir o anúncio",
        selection_options,
        format_func=lambda idx: f"{df.loc[idx, 'name']} — {df.loc[idx, 'price']} — {df.loc[idx, 'freguesia']}"
    )

    selected = df.loc[selected_idx]
    detail_cols = st.columns(3)
    with detail_cols[0]:
        st.metric("Preço", selected["price"])
    with detail_cols[1]:
        st.metric("€/m²", selected["price_m2"])
    with detail_cols[2]:
        st.metric("Score", selected["score"])

    st.markdown(f"**Título:** {selected['name']}")
    st.markdown(f"**Freguesia:** {selected['freguesia']}")
    st.markdown(f"**Portal:** {selected['portal']}")
    if selected.get("url"):
        st.link_button(" Abrir anúncio original", selected["url"])

    display_cols = ["name", "price", "price_m2", "area", "freguesia", "score", "portal", "url"]
    display_df = df[display_cols].copy()
    display_df.columns = ["Título", "Preço", "€/m²", "Área", "Freguesia", "Score", "Portal", ""]
    
    st.dataframe(
        display_df, 
        width="stretch", 
        hide_index=True,
        column_config={
            "": st.column_config.LinkColumn("Link", display_text="Ver"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
        }
    )
