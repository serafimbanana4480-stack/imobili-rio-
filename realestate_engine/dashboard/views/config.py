"""Settings and configuration page for dashboard."""
import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.utils.config import config
from realestate_engine.database.repository import DatabaseRepository

def render_config():
    """Render settings dashboard page."""
    st.title("⚙️ Configuração")
    st.markdown("*Configuração de parâmetros do sistema e preferências*")

    repo = DatabaseRepository()

    tab_search, tab_scoring, tab_telegram, tab_ollama = st.tabs([
        "🔍 Pesquisa", "⭐ Scoring", "📱 Telegram", "🤖 Ollama"
    ])

    # ── Search Parameters Tab ──────────────────────────────────────────────
    with tab_search:
        with st.form("search_config_form"):
            st.subheader("Parâmetros de Pesquisa")
            active_concelhos = st.multiselect(
                "Regiões Ativas (Concelhos)",
                ["Porto", "Matosinhos", "Gaia", "Maia", "Gondomar", "Valongo"],
                default=["Porto", "Matosinhos", "Gaia", "Maia"]
            )

            col1, col2 = st.columns(2)
            with col1:
                min_price = st.number_input("Preço Mínimo (€)", value=50000, step=10000)
                min_score = st.slider("Score Mínimo para Notificação", 0.0, 10.0, 8.0, 0.1)
            with col2:
                max_price = st.number_input("Preço Máximo (€)", value=1000000, step=50000)
                max_notifs = st.number_input("Máx. Notificações Diárias", value=50)

            submitted = st.form_submit_button("💾 Guardar Configuração de Pesquisa", type="primary")
            if submitted:
                repo.set_config("concelhos_activos", active_concelhos)
                repo.set_config("preco_min", min_price)
                repo.set_config("preco_max", max_price)
                repo.set_config("min_score_notificacao", min_score)
                repo.set_config("max_notif_diarias", max_notifs)
                st.success("✅ Configuração de pesquisa guardada!")

    # ── Scoring Weights Tab ────────────────────────────────────────────────
    with tab_scoring:
        with st.form("scoring_config_form"):
            st.subheader("Pesos do Scoring")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                w_discount = st.slider("Desconto (%)", 0, 100, 45)
            with col2:
                w_location = st.slider("Localização (%)", 0, 100, 20)
            with col3:
                w_condition = st.slider("Estado (%)", 0, 100, 15)
            with col4:
                w_liquidity = st.slider("Liquidez (%)", 0, 100, 10)
            with col5:
                w_freshness = st.slider("Atualidade (%)", 0, 100, 10)

            total = w_discount + w_location + w_condition + w_liquidity + w_freshness
            if total != 100:
                st.warning(f"⚠️ Total dos pesos: {total}% (deveria ser 100%)")

            submitted = st.form_submit_button("💾 Guardar Pesos do Scoring", type="primary")
            if submitted:
                repo.set_config("scoring_weights", {
                    "discount": w_discount / 100,
                    "location": w_location / 100,
                    "condition": w_condition / 100,
                    "liquidity": w_liquidity / 100,
                    "freshness": w_freshness / 100,
                })
                st.success("✅ Pesos do scoring guardados!")

    # ── Telegram Tab ────────────────────────────────────────────────────────
    with tab_telegram:
        st.subheader("📱 Configuração Telegram")

        current_token = st.text_input("Bot Token", value=config.telegram_bot_token or "", type="password")
        current_chat_id = st.text_input("Chat ID", value=config.telegram_chat_id or "")

        if st.button("💾 Guardar Credenciais Telegram", type="primary"):
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                ".env"
            )
            try:
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                updated = {"TELEGRAM_BOT_TOKEN": False, "TELEGRAM_CHAT_ID": False}
                for i, line in enumerate(lines):
                    if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                        lines[i] = f'TELEGRAM_BOT_TOKEN="{current_token}"\n'
                        updated["TELEGRAM_BOT_TOKEN"] = True
                    elif line.strip().startswith("TELEGRAM_CHAT_ID="):
                        lines[i] = f'TELEGRAM_CHAT_ID="{current_chat_id}"\n'
                        updated["TELEGRAM_CHAT_ID"] = True

                if not updated["TELEGRAM_BOT_TOKEN"]:
                    lines.append(f'TELEGRAM_BOT_TOKEN="{current_token}"\n')
                if not updated["TELEGRAM_CHAT_ID"]:
                    lines.append(f'TELEGRAM_CHAT_ID="{current_chat_id}"\n')

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                st.success("✅ Credenciais Telegram guardadas no .env! Reinicia para aplicar.")
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")

    # ── Ollama Tab ──────────────────────────────────────────────────────────
    with tab_ollama:
        st.subheader("🤖 Configuração Ollama")

        st.markdown("""
        O modelo Ollama é usado para gerar teses de investimento com IA.
        
        **Modelo atual:** `mistral:7b` (otimizado para Português)
        """)

        ollama_model = st.selectbox(
            "Modelo Ollama",
            ["mistral:7b", "llama3:8b", "qwen3-14b-fast", "gemma2:9b"],
            index=0,
            help="Seleciona o modelo para análise IA. mistral:7b é recomendado para Português."
        )

        if st.button("💾 Guardar Modelo Ollama", type="primary"):
            repo.set_config("ollama_model", ollama_model)
            st.success(f"✅ Modelo Ollama guardado: {ollama_model}")

        st.markdown("---")
        st.markdown("### 📥 Gerir Modelos")
        st.code(f"ollama pull {ollama_model}", language="bash")
        st.caption("Executa este comando no terminal para descarregar o modelo selecionado.")

    # ── System Maintenance ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔧 Manutenção do Sistema")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Limpar Cache de Geocoding"):
            st.warning("Cache limpo (simulado)")
    with col2:
        if st.button("📤 Exportar Base de Dados para CSV"):
            st.info("Exportação para data/exports/ (simulado)")

