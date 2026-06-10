"""Alert manager for Real Estate Opportunity Engine."""
from typing import Optional
from loguru import logger

from realestate_engine.utils.config import config


class AlertManager:
    """Manages alerts and notifications for system failures."""
    
    def __init__(self):
        self.telegram_enabled = bool(config.telegram_bot_token and config.telegram_chat_id)
    
    async def send_alert(self, message: str) -> bool:
        """Send alert via available channels."""
        logger.warning(f"ALERT: {message}")
        if self.telegram_enabled:
            try:
                from telegram import Bot
                bot = Bot(token=config.telegram_bot_token)
                await bot.send_message(chat_id=config.telegram_chat_id, text=f"ALERT: {message}")
                return True
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
        return False
    
    def send_alert_sync(self, message: str) -> bool:
        """Send alert synchronously."""
        logger.warning(f"ALERT: {message}")
        return True
