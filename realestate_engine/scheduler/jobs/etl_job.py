"""ETL job for Real Estate Opportunity Engine."""
import asyncio
from loguru import logger

from realestate_engine.utils.decorators import async_retry
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


class ETLJob:
    """Executes ETL pipeline."""
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
    
    @async_retry(max_attempts=2, delay=3)
    async def run(self) -> int:
        """Run ETL job and return number of listings processed."""
        logger.info("Starting ETL job")
        
        if self.pipeline is None:
            from realestate_engine.etl.pipeline_etl import PipelineETL
            self.pipeline = PipelineETL()
        
        try:
            count = await self.pipeline.run()
            metrics.record_listings_processed("etl", count)
            logger.info(f"ETL job completed: {count} listings processed")
            return count
        except Exception as e:
            logger.error(f"ETL job failed: {e}")
            raise
