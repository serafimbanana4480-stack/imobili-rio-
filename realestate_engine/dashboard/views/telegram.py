"""Telegram bot management page for dashboard."""
import streamlit as st
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.utils.config import config
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.notification.telegram_bot import TelegramBot


def _run_async(coro):
    """Run an async coroutine in Streamlit context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def render_telegram():
    """Render Telegram management dashboard page."""
    st.title(" Telegram Bot")
    st.markdown("*Gestão do bot Telegram e histórico de notificações*")

    repo = DatabaseRepository()

    #  Bot Status Card 
    st.markdown("###  Estado do Bot")

    token = config.telegram_bot_token
    chat_id = config.telegram_chat_id

    # Check bot status
    bot_status = "desconhecido"
    bot_info = {}
    if token and token != "your_bot_token_here":
        try:
            import httpx
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def _check():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                    return r.json()
            result = loop.run_until_complete(_check())
            loop.close()
            if result.get("ok"):
                bot_info = result.get("result", {})
                bot_status = "online"
            else:
                bot_status = "erro"
        except Exception:
            bot_status = "erro"
    else:
        bot_status = "não configurado"

    col1, col2, col3 = st.columns(3)
    with col1:
        status_emoji = {"online": "", "erro": "", "não configurado": "", "desconhecido": ""}
        status_class = {"online": "success", "erro": "error", "não configurado": "warning", "desconhecido": "warning"}
        st.metric("Bot", f"{status_emoji.get(bot_status, '')} {bot_status.upper()}")
    with col2:
        if bot_info:
            st.metric("Username", f"@{bot_info.get('username', 'N/A')}")
        else:
            st.metric("Username", "N/A")
    with col3:
        chat_status = " Configurado" if chat_id and chat_id != "your_chat_id_here" else " Em falta"
        st.metric("Chat ID", chat_status)

    #  Configuration Section 
    st.markdown("---")
    st.markdown("###  Configuração")

    with st.expander(" Credenciais do Bot", expanded=not token or token == "your_bot_token_here"):
        st.info("Obtém o token do @BotFather e o Chat ID do @userinfobot no Telegram")

        current_token = st.text_input("Bot Token", value=token or "", type="password")
        current_chat_id = st.text_input("Chat ID", value=chat_id or "")

        if st.button(" Guardar Credenciais", type="primary"):
            if current_token:
                # Update .env file
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

                    st.success(" Credenciais guardadas no .env! Reinicia a app para aplicar.")
                except Exception as e:
                    st.error(f"Erro ao guardar: {e}")
            else:
                st.warning("Token não pode estar vazio")

    #  Chat ID Detection 
    with st.expander(" Detetar Chat ID Automaticamente"):
        st.markdown("""
        Para receber notificações, precisas do teu **Chat ID** pessoal:
        
        1. Abre o Telegram e envia `/start` ao bot **@testbotprojeto_bot**
        2. Clica no botão abaixo para detetar o Chat ID
        """)
        if st.button(" Detetar Chat ID", type="primary"):
            if token and token != "your_bot_token_here":
                with st.spinner("A verificar mensagens..."):
                    try:
                        import httpx
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        async def _detect():
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                r = await client.get(f"https://api.telegram.org/bot{token}/getUpdates")
                                return r.json()
                        result = loop.run_until_complete(_detect())
                        loop.close()
                        updates = result.get("result", [])
                        if updates:
                            for update in updates[-5:]:
                                msg = update.get("message", {})
                                chat = msg.get("chat", {})
                                cid = chat.get("id")
                                ctype = chat.get("type")
                                first = chat.get("first_name", "Unknown")
                                st.markdown(f"""
                                <div class="re-card">
                                    <b>Chat ID:</b> <code>{cid}</code><br/>
                                    <b>Tipo:</b> {ctype}<br/>
                                    <b>Nome:</b> {first}
                                </div>
                                """, unsafe_allow_html=True)
                            st.info(f"Adiciona `TELEGRAM_CHAT_ID=\"{updates[-1]['message']['chat']['id']}\"` ao .env")
                        else:
                            st.warning(" Nenhuma mensagem encontrada. Envia /start ao bot @testbotprojeto_bot primeiro.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
            else:
                st.warning("Configura o token primeiro")

    #  Test Message 
    st.markdown("---")
    st.markdown("###  Teste de Mensagem")

    test_msg = st.text_area("Mensagem de teste", value=" *Real Estate Engine Test*\nNotificação de teste do dashboard local.")

    if st.button(" Enviar Mensagem de Teste", type="primary"):
        if token and chat_id and chat_id != "your_chat_id_here":
            with st.spinner("A enviar..."):
                bot = TelegramBot(token=token, chat_id=chat_id)
                result = _run_async(bot.send_message(test_msg))
                if result:
                    st.success(f" Mensagem enviada! ID: {result}")
                else:
                    st.error(" Falha ao enviar. Verifica token e Chat ID.")
        else:
            st.warning("Configura token e Chat ID primeiro")

    #  AI Analysis Notification 
    st.markdown("---")
    st.markdown("###  Análise IA via Telegram")

    if st.button(" Enviar Análise IA das Top 3 Oportunidades", type="primary"):
        if token and chat_id and chat_id != "your_chat_id_here":
            with st.spinner("A IA está a analisar e enviar notificações... (pode demorar alguns minutos)"):
                try:
                    from realestate_engine.notification.notification_engine import NotificationEngine
                    notifier = NotificationEngine()
                    sent = _run_async(notifier.notify_ai_analysis(limit=3))
                    if sent > 0:
                        st.success(f" {sent} análises IA enviadas para o Telegram!")
                    else:
                        st.warning("Nenhuma oportunidade encontrada para análise")
                except Exception as e:
                    st.error(f"Erro na análise IA: {e}")
                    st.info("Certifica-te de que o Ollama está a correr com o modelo mistral:7b")
        else:
            st.warning("Configura token e Chat ID primeiro")

    #  Notification History 
    st.markdown("---")
    st.markdown("###  Histórico de Notificações")

    notifications = repo.get_pending_notifications(limit=50)
    if notifications:
        import pandas as pd
        data = []
        for n in notifications:
            data.append({
                "Data": n.sent_at.strftime("%Y-%m-%d %H:%M") if n.sent_at else "Pendente",
                "Estado": n.status.upper(),
                "Mensagem": (n.message or "")[:80] + "..." if n.message and len(n.message) > 80 else (n.message or ""),
                "Erro": n.error_message or "",
            })
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Sem notificações no histórico. Executa o pipeline para gerar oportunidades.")

