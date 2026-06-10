"""AI Best Deals view for dashboard."""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer
from realestate_engine.dashboard.utils.async_helpers import _run_async
from realestate_engine.dashboard.utils.theme import score_badge, PRIMARY_COLOR, is_dark_mode, TEXT_COLOR_MUTED_DARK, TEXT_COLOR_MUTED_LIGHT


def render_ai_deals():
    st.title("🤖 Assistente IA de Oportunidades")
    st.markdown(
        "*Leitura executiva das melhores oportunidades, com linguagem de consultoria e fallback local transparente quando a IA não está disponível.*"
    )

    st.info(
        "Aqui encontras uma leitura curta e acionável: o que interessa, porque interessa e qual o próximo passo recomendado."
    )

    # ── Model Info ────────────────────────────────────────────────────────
    with st.expander("ℹ️ Informações do Modelo", expanded=False):
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

    # ── Number of deals selector ──────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        num_deals = st.slider("Quantas oportunidades queres rever", min_value=1, max_value=10, value=3)
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🚀 Gerar leitura executiva", type="primary"):
            with st.spinner("A preparar a leitura executiva... isto pode demorar alguns instantes."):
                analyzer = OpportunityAnalyzer()
                try:
                    deals = _run_async(analyzer.get_top_deals_report(limit=num_deals))
                    st.session_state.ai_deals = deals
                except Exception as e:
                    st.error(f"Não foi possível gerar a leitura executiva: {e}")
                    st.info("Confirma se o Ollama está ativo localmente com o modelo `mistral:7b`.")

    # ── Display Results ───────────────────────────────────────────────────
    if 'ai_deals' in st.session_state and st.session_state.ai_deals:
        st.markdown("---")
        st.markdown(f"### 🏆 Top {len(st.session_state.ai_deals)} oportunidades com maior potencial")
        st.caption("Cada cartão resume o racional comercial, a origem da análise e o próximo passo recomendado.")

        for i, deal in enumerate(st.session_state.ai_deals, 1):
            with st.container():
                # Header row with score and discount
                col_header, col_link = st.columns([4, 1])
                with col_header:
                    source = deal.get("analysis_source", "unknown")
                    if source == "ollama":
                        source_label = "Análise IA"
                        source_color = "#10B981"
                    elif source == "ollama_cache":
                        source_label = "Análise IA (cache)"
                        source_color = "#10B981"
                    else:
                        source_label = "Leitura assistida local"
                        source_color = "#F59E0B"
                    diag = deal.get("analysis_diagnostic")
                    st.markdown(f"""
                    <div class="re-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-size:1.1em;font-weight:700;">{i}. {deal['title']}</span>
                            {score_badge(deal['score'])}
                        </div>
                        <div style="display:flex;gap:16px;margin-bottom:8px;">
                            <span style="color:#10B981;font-weight:600;">📉 Margem estimada: {deal['discount']*100:.1f}%</span>
                            <span style="color:{source_color};font-weight:600;">🧠 Origem: {source_label}</span>
                        </div>
                        <div style="color:{TEXT_COLOR_MUTED_DARK if is_dark_mode() else TEXT_COLOR_MUTED_LIGHT};font-size:0.92rem;">
                            Leitura rápida para decisão: prioriza este ativo se quiseres capturar margem com validação humana curta.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_link:
                    if deal.get('url'):
                        st.link_button("🔗 Abrir anúncio", deal['url'])

                # Expandable thesis section
                with st.expander("📖 Resumo executivo", expanded=i <= 2):
                    if source != "ollama":
                        st.warning("A leitura abaixo foi produzida pelo fallback local para não bloquear a decisão.")
                        if diag:
                            st.caption(f"Diagnóstico: {diag}")
                    thesis = deal.get('thesis', 'Sem tese disponível')
                    st.markdown(thesis)

                    st.markdown("**O que fazer a seguir:** verificar localização, confrontar comparáveis e confirmar estado físico antes de avançar.")

                st.markdown("---")
    else:
        st.info("Clica em **🚀 Gerar leitura executiva** para receber a análise das melhores oportunidades.")

