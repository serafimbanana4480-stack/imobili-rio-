"""Watchlist page for dashboard.

User's saved properties with notes and tags.
"""
import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.database.repository import DatabaseRepository


def render_watchlist():
    """Render watchlist page."""
    st.title(" Minha Watchlist")
    st.markdown("*Propriedades guardadas para análise futura*")

    repo = DatabaseRepository()

    # Get watchlist
    watchlist = repo.get_watchlist()

    if not watchlist:
        st.info("A sua watchlist está vazia. Adicione propriedades a partir da página de pesquisa ou overview.")
        return

    # KPI summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", f"{len(watchlist)}")
    with col2:
        avg_price = sum(l.preco_pedido for l in watchlist if l.preco_pedido) / len(watchlist)
        st.metric("Preço Médio", f"{avg_price:,.0f}€".replace(",", "."))
    with col3:
        avg_m2 = sum(l.preco_por_m2 for l in watchlist if l.preco_por_m2) / len([l for l in watchlist if l.preco_por_m2])
        st.metric("€/m² Médio", f"{avg_m2:,.0f}€".replace(",", "."))

    st.markdown("---")

    # Build dataframe
    data = []
    for l in watchlist:
        score = repo.get_score_by_listing(l.id)
        
        data.append({
            "": "",
            "": score.classificacao if score else "",
            "Score": score.score_total if score else 0,
            "Título": (l.titulo or "")[:50],
            "Preço": f"{l.preco_pedido:,.0f}€".replace(",", ".") if l.preco_pedido else "",
            "€/m²": f"{l.preco_por_m2:,.0f}€".replace(",", ".") if l.preco_por_m2 else "",
            "Área": f"{l.area_util_m2:.0f}m²" if l.area_util_m2 else "",
            "Freguesia": l.freguesia or "",
            "Portal": l.source_portal,
            " Link": l.source_url or "",
            "_id": l.id,
        })

    df = pd.DataFrame(data)
    
    # Sort by score
    if not df.empty and "Score" in df.columns:
        df = df.sort_values(by="Score", ascending=False)

    # Display table
    st.dataframe(
        df, 
        width="stretch", 
        hide_index=True,
        column_config={
            "": st.column_config.TextColumn("Watchlist", width="small"),
            " Link": st.column_config.LinkColumn("Link", display_text="Ver"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "_id": None,
        }
    )

    # Bulk actions
    st.markdown("---")
    st.subheader(" Ações em Massa")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Comparar Selecionados", type="primary"):
            st.info("Funcionalidade de comparação em desenvolvimento.")
    
    with col2:
        if st.button(" Limpar Watchlist", type="secondary"):
            if st.session_state.get('confirm_clear', False):
                # Remove all from watchlist
                for l in watchlist:
                    repo.remove_from_watchlist(l.id)
                st.success("Watchlist limpa com sucesso!")
                st.rerun()
            else:
                st.session_state['confirm_clear'] = True
                st.warning("Clique novamente para confirmar a limpeza da watchlist.")

    # Export functionality
    st.markdown("---")
    st.subheader(" Exportar")
    
    export_format = st.selectbox("Formato", ["CSV", "Excel"])
    
    if st.button(" Exportar Watchlist"):
        if export_format == "CSV":
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="watchlist.csv",
                mime="text/csv"
            )
        else:
            # Excel export would require openpyxl
            st.info("Exportação Excel requer biblioteca adicional (openpyxl)")
