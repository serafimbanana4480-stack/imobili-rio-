"""Script para obter Chat ID do Telegram via API."""
import httpx
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.utils.config import config

async def get_chat_id():
    """Obtém Chat ID das últimas mensagens do bot."""
    token = config.telegram_bot_token
    if not token:
        print("❌ Token não configurado")
        return

    print("📡 A obter Chat ID do Telegram...")
    print(f"🔑 Token: {token[:20]}...")
    print()
    print("⚠️  Certifica-te de que enviaste /start ao bot @testbotprojeto_bot")
    print()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"https://api.telegram.org/bot{token}/getUpdates")
        result = response.json()

        if not result.get("ok"):
            print(f"❌ Erro: {result}")
            return

        updates = result.get("result", [])
        if not updates:
            print("❌ Nenhuma mensagem encontrada.")
            print("💡 Envia /start ao bot @testbotprojeto_bot primeiro")
            return

        print(f"✅ Encontradas {len(updates)} mensagens")
        print()

        # Mostrar últimas 5 mensagens
        for update in updates[-5:]:
            msg = update.get("message", {})
            chat = msg.get("chat", {})
            cid = chat.get("id")
            ctype = chat.get("type")
            first = chat.get("first_name", "Unknown")
            username = chat.get("username", "")

            print(f"📨 Chat ID: {cid}")
            print(f"   Tipo: {ctype}")
            print(f"   Nome: {first}")
            if username:
                print(f"   Username: @{username}")
            print()

        # Último Chat ID
        last_chat_id = updates[-1]["message"]["chat"]["id"]
        print(f"🎯 Usa este Chat ID: {last_chat_id}")
        print(f"📝 Adiciona ao .env: TELEGRAM_CHAT_ID=\"{last_chat_id}\"")

if __name__ == "__main__":
    asyncio.run(get_chat_id())
