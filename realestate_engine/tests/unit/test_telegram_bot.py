"""Unit tests for TelegramBot."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from realestate_engine.notification.telegram_bot import TelegramBot


class TestTelegramBot:
    """Test Telegram bot functions."""

    def test_init_without_token(self):
        bot = TelegramBot(token="", chat_id="")
        assert bot._bot is None

    def test_init_with_token(self):
        with patch("realestate_engine.notification.telegram_bot.TELEGRAM_AVAILABLE", True):
            with patch("realestate_engine.notification.telegram_bot.Bot") as MockBot:
                bot = TelegramBot(token="test_token", chat_id="12345")
                MockBot.assert_called_once_with(token="test_token")

    @pytest.mark.asyncio
    async def test_send_message_not_configured(self):
        bot = TelegramBot(token="", chat_id="")
        result = await bot.send_message("Hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        with patch("realestate_engine.notification.telegram_bot.TELEGRAM_AVAILABLE", True):
            mock_bot_instance = MagicMock()
            mock_msg = MagicMock()
            mock_msg.message_id = 123
            mock_bot_instance.send_message = AsyncMock(return_value=mock_msg)

            with patch("realestate_engine.notification.telegram_bot.Bot", return_value=mock_bot_instance):
                bot = TelegramBot(token="test_token", chat_id="12345")
                result = await bot.send_message("Hello")
                assert result == "123"
                mock_bot_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        with patch("realestate_engine.notification.telegram_bot.TELEGRAM_AVAILABLE", True):
            mock_bot_instance = MagicMock()
            mock_bot_instance.send_message = AsyncMock(side_effect=Exception("Network error"))

            with patch("realestate_engine.notification.telegram_bot.Bot", return_value=mock_bot_instance):
                bot = TelegramBot(token="test_token", chat_id="12345")
                result = await bot.send_message("Hello")
                assert result is None

    @pytest.mark.asyncio
    async def test_send_opportunities(self):
        with patch("realestate_engine.notification.telegram_bot.TELEGRAM_AVAILABLE", True):
            mock_bot_instance = MagicMock()
            mock_msg = MagicMock()
            mock_msg.message_id = 1
            mock_bot_instance.send_message = AsyncMock(return_value=mock_msg)

            with patch("realestate_engine.notification.telegram_bot.Bot", return_value=mock_bot_instance):
                bot = TelegramBot(token="test_token", chat_id="12345")
                messages = ["Msg1", "Msg2", "Msg3"]
                result = await bot.send_opportunities(messages)
                assert result == 3
                assert mock_bot_instance.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_send_opportunities_partial_failure(self):
        with patch("realestate_engine.notification.telegram_bot.TELEGRAM_AVAILABLE", True):
            mock_bot_instance = MagicMock()
            mock_msg = MagicMock()
            mock_msg.message_id = 1
            mock_bot_instance.send_message = AsyncMock(side_effect=[mock_msg, None, mock_msg])

            with patch("realestate_engine.notification.telegram_bot.Bot", return_value=mock_bot_instance):
                bot = TelegramBot(token="test_token", chat_id="12345")
                messages = ["Msg1", "Msg2", "Msg3"]
                result = await bot.send_opportunities(messages)
                assert result == 2
