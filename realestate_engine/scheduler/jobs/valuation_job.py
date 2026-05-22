"""Valuation job for Real Estate Opportunity Engine."""
import asyncio
from loguru import logger

from realestate_engine.utils.decorators import async_retry
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


class ValuationJob:
    """Executes valuation for unvaluated listings."""
    
    def __init__(self, engine=None):
        self.engine = engine
    
    @async_retry(max_attempts=2, delay=3)
    async def run(self) -> int:
        """Run valuation job and return number of valuations computed."""
        logger.info("Starting valuation job")
        
        if self.engine is None:
            from realestate_engine.valuation.valuation_engine import ValuationEngine
            self.engine = ValuationEngine()
        
        try:
            count = await self.engine.valuate_batch()
            for _ in range(count):
                metrics.record_valuation()
            logger.info(f"Valuation job completed: {count} valuations computed")
            return count
        except Exception as e:
            logger.error(f"Valuation job failed: {e}")
            raise
