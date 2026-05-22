"""Script para testar envio de mensagem Telegram."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.notification.telegram_bot import TelegramBot

async def test_send():
    """Testa envio de mensagem."""
    bot = TelegramBot()
    
    print("📱 Telegram Bot Test")
    print(f"Token: {'✅' if bot.token else '❌'}")
    print(f"Chat ID: {'✅' if bot.chat_id else '❌'}")
    print(f"Bot inicializado: {'✅' if bot._bot else '❌'}")
    print()
    
    if not bot.chat_id:
        print("❌ Chat ID não configurado")
        return
    
    print("📤 A enviar mensagem de teste...")
    
    msg = """🏠 *Real Estate Engine - Teste*

✅ Bot Telegram configurado com sucesso!

🔹 Token: Configurado
🔹 Chat ID: Configurado
🔹 Sistema: Pronto para enviar notificações

Esta é uma mensagem de teste para verificar que o bot está a funcionar corretamente."""
    
    result = await bot.send_message(msg)
    
    if result:
        print(f"✅ Mensagem enviada com sucesso! ID: {result}")
    else:
        print("❌ Falha ao enviar mensagem")

if __name__ == "__main__":
    asyncio.run(test_send())
