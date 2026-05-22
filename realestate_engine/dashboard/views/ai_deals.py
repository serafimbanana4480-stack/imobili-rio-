"""AI Best Deals view for dashboard."""
import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer, clear_cache
from realestate_engine.dashboard.utils.theme import score_badge, PRIMARY_COLOR


def _run_async(coro):
    """Run an async coroutine in Streamlit context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def render_ai_deals():
    st.title(" Assistente IA de Oportunidades")
    st.markdown(
        "*Leitura executiva das melhores oportunidades, com linguagem de consultoria e fallback local transparente quando a IA não está disponível.*"
    )

    st.info(
        "Aqui encontras uma leitura curta e acionável: o que interessa, porque interessa e qual o próximo passo recomendado."
    )

    #  Model Info 
    with st.expander("ℹ Informações do Modelo", expanded=False):
        st.markdown("""
        **Leitura:** tese de investimento em linguagem clara, com foco em decisão  
        **Base analítica:** desconto, localização, robustez do valuation e potencial de valorização  
        **Origem da tese:** Ollama local quando disponível; fallback local quando necessário  
        **Objetivo:** ajudar-te a filtrar rapidamente o que merece revisão humana prioritária  
        
        Para usar esta funcionalidade, o Ollama deve estar a correr localmente:
        ```bash
        ollama serve
        ollama pull mistral:7b
        ```
        """)

    #  Controls 
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        num_deals = st.slider("Quantas oportunidades", min_value=1, max_value=10, value=3)
    with col2:
        force_refresh = st.checkbox(" Forçar refresh", help="Ignora cache e gera nova análise (demora mais)")
    with col3:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button(" Limpar cache"):
            deleted = clear_cache()
            st.success(f"Cache limpo ({deleted} ficheiros)")
            st.rerun()
    
    #  Filters 
    with st.expander(" Filtros Avançados", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_freguesia = st.text_input("Freguesia (opcional)", placeholder="ex: Campanhã, Bonfim")
        with col2:
            filter_tipologia = st.selectbox("Tipologia (opcional)", ["Todas", "T1", "T2", "T3", "T4+"])
        with col3:
            col_price1, col_price2 = st.columns(2)
            with col_price1:
                min_price = st.number_input("Preço min (€)", min_value=0, value=0, step=10000)
            with col_price2:
                max_price = st.number_input("Preço max (€)", min_value=0, value=0, step=10000)
    
    if st.button(" Gerar leitura executiva", type="primary"):
        with st.spinner("A preparar a leitura executiva... isto pode demorar alguns instantes." + (" (sem cache)" if force_refresh else "")):
            analyzer = OpportunityAnalyzer()
            try:
                # Prepare filter parameters
                freguesia_filter = filter_freguesia if filter_freguesia else None
                tipologia_filter = filter_tipologia if filter_tipologia != "Todas" else None
                min_price_filter = min_price if min_price > 0 else None
                max_price_filter = max_price if max_price > 0 else None
                
                deals = _run_async(analyzer.get_top_deals_report(
                    limit=num_deals, 
                    force_refresh=force_refresh,
                    freguesia=freguesia_filter,
                    tipologia=tipologia_filter,
                    min_price=min_price_filter,
                    max_price=max_price_filter
                ))
                st.session_state.ai_deals = deals
                st.session_state.ai_deals_generated_at = datetime.now()
            except Exception as e:
                st.error(f"Não foi possível gerar a leitura executiva: {e}")
                st.info("Confirma se o Ollama está ativo localmente com o modelo `mistral:7b`.")

    #  Display Results 
    if 'ai_deals' in st.session_state and st.session_state.ai_deals:
        st.markdown("---")
        
        # Show generation timestamp
        if 'ai_deals_generated_at' in st.session_state:
            generated_at = st.session_state.ai_deals_generated_at
            time_ago = (datetime.now() - generated_at).total_seconds()
            if time_ago < 60:
                time_str = "agora"
            elif time_ago < 3600:
                time_str = f"há {int(time_ago/60)} min"
            else:
                time_str = f"há {int(time_ago/3600)}h"
            st.caption(f" Análise gerada {time_str}")
        
        st.markdown(f"###  Top {len(st.session_state.ai_deals)} oportunidades com maior potencial")
        st.caption("Cada cartão resume o racional comercial, a origem da análise e o próximo passo recomendado.")

        for i, deal in enumerate(st.session_state.ai_deals, 1):
            with st.container():
                # Header row with score and discount
                col_header, col_link = st.columns([4, 1])
                with col_header:
                    source = deal.get("analysis_source", "unknown")
                    created_at = deal.get("created_at")
                    
                    # Build freshness label
                    if source == "ollama":
                        source_label = "Análise IA"
                        source_color = "#10B981"
                        freshness = "(agora)"
                    elif source == "ollama_cache":
                        source_label = "Análise IA (cache)"
                        source_color = "#3B82F6"
                        if created_at and created_at != "unknown":
                            try:
                                from datetime import timezone
                                cache_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
                                if age_hours < 1:
                                    freshness = "(< 1h)"
                                else:
                                    freshness = f"({int(age_hours)}h)"
                            except Exception:
                                freshness = ""
                        else:
                            freshness = ""
                    else:
                        source_label = "Leitura assistida local"
                        source_color = "#F59E0B"
                        freshness = ""
                    
                    # Market context comparison
                    preco_por_m2 = deal.get("preco_por_m2", 0)
                    median_price_m2 = deal.get("median_price_m2", 0)
                    if median_price_m2 > 0:
                        vs_median_pct = ((preco_por_m2 / median_price_m2 - 1) * 100)
                        if vs_median_pct < -5:
                            vs_median_color = "#10B981"  # Green - below average
                            vs_median_label = f" {vs_median_pct:+.1f}% vs média"
                        elif vs_median_pct > 5:
                            vs_median_color = "#EF4444"  # Red - above average
                            vs_median_label = f" {vs_median_pct:+.1f}% vs média"
                        else:
                            vs_median_color = "#6B7280"  # Gray - near average
                            vs_median_label = f" {vs_median_pct:+.1f}% vs média"
                    else:
                        vs_median_color = "#6B7280"
                        vs_median_label = "N/A vs média"
                    
                    yoy_variation = deal.get("yoy_variation", 0)
                    trend_emoji = "" if yoy_variation > 0 else "" if yoy_variation < 0 else ""
                    trend_label = f"{trend_emoji} {yoy_variation:+.1f}% anual"
                    
                    market_activity = deal.get("market_activity", "N/D")
                    
                    diag = deal.get("analysis_diagnostic")
                    st.markdown(f"""
                    <div class="re-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-size:1.1em;font-weight:700;">{i}. {deal['title']}</span>
                            {score_badge(deal['score'])}
                        </div>
                        <div style="display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap;">
                            <span style="color:#10B981;font-weight:600;"> Margem: {deal['discount']*100:.1f}%</span>
                            <span style="color:{source_color};font-weight:600;"> {source_label} {freshness}</span>
                            <span style="color:{vs_median_color};font-weight:600;">{vs_median_label}</span>
                            <span style="color:#6B7280;font-weight:600;">{trend_label}</span>
                            <span style="color:#6B7280;font-size:0.9em;"> {deal.get('freguesia', 'N/D')}</span>
                        </div>
                        <div style="color:#6B7280;font-size:0.85rem;margin-top:4px;">
                            Preço: {deal.get('preco_pedido', 0):,.0f}€ | {preco_por_m2:,.0f}€/m² | Mercado: {market_activity}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_link:
                    if deal.get('url'):
                        st.link_button(" Abrir anúncio", deal['url'])

                # Expandable thesis section
                with st.expander(" Resumo executivo", expanded=i <= 2):
                    if source != "ollama":
                        st.warning("A leitura abaixo foi produzida pelo fallback local para não bloquear a decisão.")
                        if diag:
                            st.caption(f"Diagnóstico: {diag}")
                    elif source == "ollama_cache" and freshness:
                        st.info(f" Análise em cache {freshness} — clicar em ' Forçar refresh' para nova análise com Ollama")
                    thesis = deal.get('thesis', 'Sem tese disponível')
                    st.markdown(thesis)

                    st.markdown("**O que fazer a seguir:** verificar localização, confrontar comparáveis e confirmar estado físico antes de avançar.")

                st.markdown("---")
    else:
        st.info("Clica em ** Gerar leitura executiva** para receber a análise das melhores oportunidades.")

