"""Script para testar token do Telegram e obter Chat ID automaticamente."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

# Carregar .env explicitamente
load_dotenv()

async def test_token_and_get_chat_id():
    """Testar token do Telegram e obter Chat ID via API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    logger.info(f"Token do .env: {token}")
    
    if not token or token == "your_bot_token_here":
        logger.error("Token não configurado no .env")
        logger.info("Verifica se o ficheiro .env existe no diretório raiz do projeto")
        return
    
    logger.info(f"Token configurado: {token[:20]}...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Testar getMe para verificar se o token é válido
            response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result")
                    logger.info(f"✅ Token válido!")
                    logger.info(f"   Bot ID: {bot_info.get('id')}")
                    logger.info(f"   Bot Username: @{bot_info.get('username')}")
                    logger.info(f"   Bot Name: {bot_info.get('first_name')}")
                    
                    # Tentar obter updates para ver se há mensagens recentes
                    logger.info("\n📡 A verificar se há mensagens recentes...")
                    response = await client.get(f"https://api.telegram.org/bot{token}/getUpdates")
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            if updates:
                                logger.info(f"✅ Encontradas {len(updates)} mensagens recentes")
                                for update in updates[-5:]:  # Mostrar últimas 5
                                    message = update.get("message", {})
                                    chat = message.get("chat", {})
                                    logger.info(f"   Chat ID: {chat.get('id')}")
                                    logger.info(f"   Chat Type: {chat.get('type')}")
                                    logger.info(f"   From: {chat.get('first_name', 'Unknown')}")
                                    logger.info(f"   Message: {message.get('text', 'No text')[:50]}...")
                                    logger.info("---")
                                # Usar o Chat ID mais recente
                                last_chat_id = updates[-1].get("message", {}).get("chat", {}).get("id")
                                logger.info(f"\n💡 Para configurar, adiciona ao .env:")
                                logger.info(f'   TELEGRAM_CHAT_ID="{last_chat_id}"')
                            else:
                                logger.info("⚠️  Nenhuma mensagem recente encontrada")
                                logger.info("💡 Envia uma mensagem ao bot @testbotprojeto_bot e executa este script novamente")
                    else:
                        logger.error(f"Erro ao obter updates: {response.text}")
                else:
                    logger.error(f"Token inválido: {data.get('description')}")
            else:
                logger.error(f"Erro na API: {response.status_code}")
    except Exception as e:
        logger.error(f"Erro ao testar token: {e}")

if __name__ == "__main__":
    asyncio.run(test_token_and_get_chat_id())
