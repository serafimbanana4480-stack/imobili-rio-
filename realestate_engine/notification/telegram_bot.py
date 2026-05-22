"""Telegram bot integration with rate-limit aware retry."""
import asyncio
from typing import Optional
from loguru import logger

try:
    from telegram import Bot
    from telegram.constants import ParseMode
    from telegram.error import (
        RetryAfter,
        TimedOut,
        NetworkError,
        Forbidden,
        InvalidToken,
        BadRequest,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Stub the error classes so isinstance checks don't blow up when
    # python-telegram-bot is absent (slim install).
    class RetryAfter(Exception):  # type: ignore[no-redef]
        retry_after: int = 0
    class TimedOut(Exception): pass        # type: ignore[no-redef]
    class NetworkError(Exception): pass    # type: ignore[no-redef]
    class Forbidden(Exception): pass       # type: ignore[no-redef]
    class InvalidToken(Exception): pass    # type: ignore[no-redef]
    class BadRequest(Exception): pass      # type: ignore[no-redef]
    logger.warning("python-telegram-bot not installed")

from realestate_engine.utils.config import config
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

# Cap how long we honour Telegram's Retry-After. Above this, we give up on
# this attempt rather than block the orchestrator for minutes.
MAX_RETRY_AFTER_S = 60


class TelegramBot:
    """Telegram bot for sending notifications.

    Hardening (Onda 4):
    - ``RetryAfter`` (HTTP 429) honoured with the server's wait hint up to
      ``MAX_RETRY_AFTER_S``; longer waits short-circuit so a rate-limit storm
      doesn't pin the orchestrator.
    - ``Forbidden`` / ``InvalidToken`` are non-recoverable: we log loudly
      and stop trying instead of looping retries that will never succeed.
    - ``TimedOut`` / ``NetworkError`` are transient: handled by the upstream
      retry in :class:`NotificationEngine`.
    """

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or config.telegram_bot_token
        self.chat_id = chat_id or config.telegram_chat_id
        self._bot: Optional[Bot] = None

        if TELEGRAM_AVAILABLE and self.token:
            self._bot = Bot(token=self.token)

    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to the configured chat.

        Returns the Telegram message id on success, or ``None`` on any
        failure (transient or terminal). Callers retry transient failures;
        terminal failures are logged here so they show up in error.log.
        """
        if not self._bot or not self.chat_id:
            logger.warning("Telegram bot not configured")
            return None

        try:
            msg = await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
            metrics.record_notification("telegram")
            logger.info(f"Telegram message sent: {msg.message_id}")
            return str(msg.message_id)
        except RetryAfter as e:
            wait = min(int(getattr(e, "retry_after", 1) or 1), MAX_RETRY_AFTER_S)
            logger.warning(
                f"Telegram rate-limited (429); honouring Retry-After={wait}s"
            )
            await asyncio.sleep(wait)
            try:
                msg = await self._bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=False,
                )
                metrics.record_notification("telegram")
                logger.info(f"Telegram message sent after rate-limit wait: {msg.message_id}")
                return str(msg.message_id)
            except Exception as inner:
                logger.error(f"Telegram still failing after Retry-After: {inner}")
                return None
        except (Forbidden, InvalidToken) as e:
            # These never recover with retries — log loudly so the operator
            # knows to fix the token/chat config.
            logger.error(
                f"Telegram permanent auth failure ({e.__class__.__name__}): {e}. "
                "Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )
            return None
        except BadRequest as e:
            # Markdown parsing errors etc. — message-specific, not transient.
            logger.error(f"Telegram BadRequest (likely Markdown formatting): {e}")
            return None
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Telegram transient network error: {e.__class__.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e.__class__.__name__}: {e}")
            return None

    async def send_opportunities(self, messages: list) -> int:
        """Send multiple opportunity messages with 1 s spacing (rate limit)."""
        sent = 0
        for msg in messages:
            result = await self.send_message(msg)
            if result:
                sent += 1
            await asyncio.sleep(1)  # Telegram allows ~30 msg/s; we stay well under.
        return sent
