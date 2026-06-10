"""Scraping job for Real Estate Opportunity Engine."""
import asyncio
from loguru import logger

from realestate_engine.utils.decorators import async_retry
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


class ScrapingJob:
    """Executes scraping of all portals."""
    
    def __init__(self, spider_manager=None):
        self.spider_manager = spider_manager
        self.results = []
    
    @async_retry(max_attempts=2, delay=5)
    async def run(self) -> int:
        """Run scraping job and return number of listings scraped."""
        logger.info("Starting scraping job")
        
        if self.spider_manager is None:
            from realestate_engine.scraping.spider_manager import SpiderManager
            self.spider_manager = SpiderManager()
        
        try:
            listings = await self.spider_manager.run_all_spiders()
            count = len(listings)
            metrics.record_listings_scraped("all", count)
            logger.info(f"Scraping job completed: {count} listings scraped")
            return count
        except Exception as e:
            logger.error(f"Scraping job failed: {e}")
            raise
