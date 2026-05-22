"""Notification job for Real Estate Opportunity Engine."""
import asyncio
from loguru import logger

from realestate_engine.utils.decorators import async_retry
from realestate_engine.monitoring.metrics import MetricsCollector
from realestate_engine.utils.config import config

metrics = MetricsCollector()


class NotificationJob:
    """Sends notifications for top opportunities."""
    
    def __init__(self, engine=None):
        self.engine = engine
    
    @async_retry(max_attempts=2, delay=5)
    async def run(self) -> int:
        """Run notification job and return number of notifications sent."""
        logger.info("Starting notification job")
        
        if self.engine is None:
            from realestate_engine.notification.notification_engine import NotificationEngine
            self.engine = NotificationEngine()
        
        try:
            count = await self.engine.notify_top_opportunities(
                min_score=config.min_score_notification,
                max_notifications=config.max_daily_notifications
            )
            for _ in range(count):
                metrics.record_notification("telegram")
            logger.info(f"Notification job completed: {count} notifications sent")
            return count
        except Exception as e:
            logger.error(f"Notification job failed: {e}")
            raise
