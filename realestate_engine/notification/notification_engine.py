"""Notification engine for sending opportunity alerts.

Enhanced with:
- Daily summary message
- Price drop alerts
- Duplicate notification prevention (per listing per day)
- Retry logic for failed sends
- Notification statistics tracking
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import Notification
from realestate_engine.notification.opportunity_selector import OpportunitySelector
from realestate_engine.notification.message_formatter import MessageFormatter
from realestate_engine.notification.telegram_bot import TelegramBot
from realestate_engine.utils.config import config
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


class NotificationEngine:
    """Orchestrates notification sending with deduplication and retry."""

    def __init__(self):
        self.selector = OpportunitySelector()
        self.formatter = MessageFormatter()
        self.bot = TelegramBot()
        self.repo = DatabaseRepository()

    async def healthcheck(self) -> bool:
        """Verify that the Telegram bot can reach the configured chat.

        Returns True if a real message was successfully sent, False otherwise.
        Never silently succeeds — callers can use this in smoke tests.
        """
        if not self.bot._bot or not self.bot.chat_id:
            logger.error("Telegram bot not configured (missing token or chat_id)")
            return False
        msg_id = await self.bot.send_message(
            "✅ Real Estate Engine — notification healthcheck OK."
        )
        return msg_id is not None

    async def send_startup_message(self) -> bool:
        """Send startup notification when scheduler begins."""
        try:
            msg = (
                "🚀 *Real Estate Engine - Scheduler Started*\n\n"
                f"⏰ Iniciado às: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "🔄 24/7 Scheduler ativo\n"
                "📊 Monitorizando mercado imobiliário do Porto\n\n"
                "A enviar notificações para oportunidades excelentes..."
            )
            if self.bot._bot:
                result = await self.bot.send_message(msg)
                logger.info("Startup notification sent")
                return result is not None
            else:
                logger.warning("Telegram bot not configured, skipping startup notification")
                return False
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
            return False

    async def notify_top_opportunities(
        self,
        min_score: float = None,
        max_notifications: int = None,
    ) -> int:
        """Select and notify top opportunities."""
        logger.info("Starting notification engine")

        opportunities = self.selector.select(min_score, max_notifications)
        if not opportunities:
            logger.info("No opportunities to notify")
            return 0

        # Filter out already-notified listings (deduplication)
        new_opportunities = []
        for opp in opportunities:
            listing_id = opp["listing"].id
            if not self._already_notified_today(listing_id):
                new_opportunities.append(opp)
            else:
                logger.debug(f"Skipping {listing_id}: already notified today")

        if not new_opportunities:
            logger.info("All opportunities already notified today")
            return 0

        # Format messages
        messages = []
        records = []
        for opp in new_opportunities:
            msg = self.formatter.format_opportunity(opp)
            messages.append(msg)

            notification = Notification(
                listing_id=opp["listing"].id,
                telegram_chat_id=config.telegram_chat_id,
                message=msg,
                status="pending",
            )
            records.append(notification)

        # Save pending notifications
        for record in records:
            self.repo.create_notification(record)

        # Send via Telegram with retry
        if self.bot._bot:
            sent_count = 0
            for i, (msg, record) in enumerate(zip(messages, records)):
                success = await self._send_with_retry(msg, max_retries=2)
                if success:
                    self.repo.update_notification_status(record.id, "sent")
                    sent_count += 1
                else:
                    self.repo.update_notification_status(
                        record.id, "failed", "Max retries exceeded"
                    )

            logger.info(f"Sent {sent_count}/{len(messages)} notifications")
            return sent_count
        else:
            logger.warning("Telegram bot not configured, skipping send")
            for record in records:
                self.repo.update_notification_status(record.id, "skipped", "Bot not configured")
            return 0

    async def send_daily_summary(self) -> bool:
        """Send daily summary of market activity."""
        try:
            total_listings = self.repo.get_total_clean_listings_count()
            total_new = self.repo.get_new_listings_today_count()
            opportunities = self.selector.select(max_notifications=10)

            msg = self.formatter.format_daily_summary(
                opportunities, total_listings, total_new
            )

            if self.bot._bot:
                result = await self.bot.send_message(msg)
                return result is not None
            return False
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False

    async def send_price_drop_alert(self, listing, old_price: float, new_price: float) -> bool:
        """Send alert when a tracked listing drops in price."""
        try:
            msg = self.formatter.format_price_drop_alert(listing, old_price, new_price)
            if self.bot._bot:
                result = await self.bot.send_message(msg)
                return result is not None
            return False
        except Exception as e:
            logger.error(f"Failed to send price drop alert: {e}")
            return False

    async def notify_ai_analysis(self, limit: int = 3) -> int:
        """Send AI analysis of top opportunities to Telegram.

        The analyzer reads ``OLLAMA_HOST`` / ``OLLAMA_MODEL`` from the
        environment (Onda 1 fix B3); we deliberately pass no overrides so a
        single ``.env`` change reaches both the dashboard view and the
        scheduled Telegram notification path.
        """
        from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer

        try:
            analyzer = OpportunityAnalyzer(provider="ollama")
            deals = await analyzer.get_top_deals_report(limit=limit)
            
            if not deals:
                logger.info("No AI deals to send")
                return 0
            
            sent_count = 0
            for deal in deals:
                msg = self.formatter.format_ai_deal(deal)
                if self.bot._bot:
                    result = await self.bot.send_message(msg)
                    if result:
                        sent_count += 1
                        logger.info(f"Sent AI analysis for deal: {deal['title'][:50]}...")
                else:
                    logger.warning("Telegram bot not configured, skipping AI notification")
            
            logger.info(f"Sent {sent_count}/{len(deals)} AI analysis notifications")
            return sent_count
        except Exception as e:
            logger.error(f"Failed to send AI analysis: {e}")
            return 0

    async def _send_with_retry(self, message: str, max_retries: int = 2) -> bool:
        """Send a message with retry logic."""
        for attempt in range(max_retries + 1):
            result = await self.bot.send_message(message)
            if result:
                return True
            if attempt < max_retries:
                wait_time = (attempt + 1) * 2
                logger.debug(f"Retry {attempt + 1}/{max_retries} in {wait_time}s")
                await asyncio.sleep(wait_time)
        return False

    def _already_notified_today(self, listing_id: str) -> bool:
        """Check if a listing was already notified today.

        Fail-closed: if the DB lookup raises, we assume the listing WAS
        already notified to avoid spamming the user. The previous "fail
        open" behaviour meant a flaky DB caused the same opportunities to
        be re-notified every hour — losing trust faster than missing one
        notification ever would.
        """
        try:
            notifications = self.repo.get_notifications_for_listing(listing_id)
            today = datetime.now(timezone.utc).date()
            for n in notifications:
                if n.sent_at and n.sent_at.date() == today and n.status == "sent":
                    return True
            return False
        except Exception as e:
            logger.error(
                f"_already_notified_today({listing_id}) lookup failed: "
                f"{e.__class__.__name__}: {e}; failing closed (treating as already-notified) "
                "to avoid duplicate spam."
            )
            return True
