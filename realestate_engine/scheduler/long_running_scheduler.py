"""Long-running scheduler for extended scraping sessions with AI analysis.

This scheduler runs scraping for extended periods (10-30 minutes) and then
performs AI analysis on the collected data before sending notifications.
"""
import asyncio
from datetime import datetime
from loguru import logger

from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.notification.notification_engine import NotificationEngine
from realestate_engine.utils.job_logger import JobLogger


class LongRunningScheduler:
    """Extended scheduler for long scraping sessions with AI analysis."""

    def __init__(self):
        self.spider_manager = SpiderManager()
        self.etl_pipeline = PipelineETL()
        self.valuation_engine = ValuationEngine()
        self.scoring_engine = ScoringEngine()
        self.notifier = NotificationEngine()

    async def run_extended_session(self, scrape_minutes: int = 20):
        """Run an extended scraping session followed by AI analysis.
        
        Args:
            scrape_minutes: Duration of scraping session in minutes (10-30)
        """
        logger.info(f"Starting extended scraping session ({scrape_minutes} minutes)")
        
        try:
            # Phase 1: Extended Scraping
            logger.info(f"Phase 1: Scraping for {scrape_minutes} minutes...")
            scrape_seconds = scrape_minutes * 60
            
            # Run scraping continuously for the specified duration
            start_time = datetime.now()
            total_scraped = 0
            
            while (datetime.now() - start_time).total_seconds() < scrape_seconds:
                try:
                    async with JobLogger("scraping.cycle") as jl:
                        summary = await self.spider_manager.run_all_cycle(
                            active_portals=["imovirtual", "casa_sapo"],
                        )
                        cycle_count = sum(summary.values()) if summary else 0
                        jl.records_processed = cycle_count
                        total_scraped += cycle_count
                        logger.info(f"Scraped {cycle_count} listings in this cycle (total: {total_scraped})")
                except Exception as e:
                    logger.error(f"Scraping cycle failed: {e}")
                
                # Wait before next cycle
                await asyncio.sleep(30)  # 30 seconds between cycles
            
            logger.info(f"Phase 1 complete: Scraped {total_scraped} listings in {scrape_minutes} minutes")

            # Phase 2: ETL
            logger.info("Phase 2: Running ETL Pipeline...")
            async with JobLogger("etl.pipeline") as jl:
                etl_count = await self.etl_pipeline.run(batch_size=10000)
                jl.records_processed = etl_count
            logger.info(f"ETL processed {etl_count} listings")

            # Phase 3: Valuation
            logger.info("Phase 3: Running Valuation Engine...")
            async with JobLogger("valuation.batch") as jl:
                val_count = await self.valuation_engine.valuate_batch(batch_size=10000)
                jl.records_processed = val_count
            logger.info(f"Valuation processed {val_count} listings")

            # Phase 4: Scoring
            logger.info("Phase 4: Running Scoring Engine...")
            async with JobLogger("scoring.batch") as jl:
                score_count = await self.scoring_engine.score_batch(batch_size=10000)
                jl.records_processed = score_count
            logger.info(f"Scoring processed {score_count} listings")

            # Phase 5: AI Analysis and Notifications
            logger.info("Phase 5: Running AI Analysis...")
            async with JobLogger("ai.analysis") as jl:
                ai_sent = await self.notifier.notify_ai_analysis(limit=5)
                jl.records_processed = ai_sent
            logger.info(f"AI Analysis sent {ai_sent} notifications")

            # Phase 6: Regular Notifications
            logger.info("Phase 6: Sending regular notifications...")
            async with JobLogger("notification.top_opps") as jl:
                sent = await self.notifier.notify_top_opportunities(
                    min_score=8.5, max_notifications=5,
                )
                jl.records_processed = int(sent or 0)
            logger.info(f"Sent {sent} regular notifications")

            logger.info("Extended session completed successfully")
            
        except Exception as e:
            logger.exception(f"Extended session failed: {e}")

    async def run_once(self, scrape_minutes: int = 20):
        """Run a single extended session and exit."""
        await self.run_extended_session(scrape_minutes=scrape_minutes)

    async def run_forever(self, interval_minutes: int = 60, scrape_minutes: int = 20):
        """Run extended sessions continuously.
        
        Args:
            interval_minutes: Time between sessions (default: 60 minutes)
            scrape_minutes: Duration of each scraping session (default: 20 minutes)
        """
        logger.info(f"Starting long-running scheduler (interval: {interval_minutes}min, scrape: {scrape_minutes}min)")
        
        # Send startup notification
        try:
            await self.notifier.send_startup_message()
        except Exception as e:
            logger.warning(f"Could not send startup notification: {e}")
        
        while True:
            try:
                await self.run_extended_session(scrape_minutes=scrape_minutes)
                logger.info(f"Waiting {interval_minutes} minutes before next session...")
                await asyncio.sleep(interval_minutes * 60)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutting down long-running scheduler...")
                break
            except Exception as e:
                logger.error(f"Session failed, retrying in 5 minutes: {e}")
                await asyncio.sleep(300)


async def main():
    """Main entry point for testing."""
    scheduler = LongRunningScheduler()
    
    # Run a single 20-minute session for testing
    await scheduler.run_once(scrape_minutes=20)


if __name__ == "__main__":
    asyncio.run(main())
