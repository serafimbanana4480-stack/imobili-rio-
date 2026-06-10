"""Scoring job for Real Estate Opportunity Engine."""
import asyncio
from loguru import logger

from realestate_engine.utils.decorators import async_retry
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


class ScoringJob:
    """Executes scoring for unscored listings."""
    
    def __init__(self, engine=None):
        self.engine = engine
    
    @async_retry(max_attempts=2, delay=3)
    async def run(self) -> int:
        """Run scoring job and return number of scores computed."""
        logger.info("Starting scoring job")
        
        if self.engine is None:
            from realestate_engine.scoring.scoring_engine import ScoringEngine
            self.engine = ScoringEngine()
        
        try:
            count = await self.engine.score_batch()
            for _ in range(count):
                metrics.record_score()
            logger.info(f"Scoring job completed: {count} scores computed")
            return count
        except Exception as e:
            logger.error(f"Scoring job failed: {e}")
            raise
