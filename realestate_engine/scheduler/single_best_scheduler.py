"""Single Best Opportunity Scheduler for 24H continuous operation.

This scheduler runs a continuous 60-minute cycle:
- Phase 1: Scraping + Clean (45 minutes)
  - Continuous scraping from multiple portals
  - Partial ETL every 5 minutes to prevent data accumulation
- Phase 2: Analysis (15 minutes)
  - Final ETL for remaining data
  - Valuation batch
  - Scoring batch
  - Selection of single best opportunity (hybrid criteria)
  - Send detailed Telegram notification with full amenities and justification

Key features:
- Hybrid selection criteria: score + discount + profit potential + location
- Realism verification to filter unrealistic deals
- 7-day deduplication to avoid repeat notifications
- Full amenity details in Telegram message (garage, pool, elevator, AC, kitchen equipment, security)
- Automatic justification generation for why the opportunity was selected
"""
import asyncio
from datetime import datetime
from loguru import logger

from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.notification.notification_engine import NotificationEngine
from realestate_engine.notification.best_opportunity_selector import BestOpportunitySelector
from realestate_engine.notification.message_formatter import MessageFormatter
from realestate_engine.notification.telegram_bot import TelegramBot
from realestate_engine.database.models import Notification
from realestate_engine.utils.job_logger import JobLogger


class SingleBestOpportunityScheduler:
    """24H continuous scheduler for single best opportunity notification."""

    def __init__(self):
        self.spider_manager = SpiderManager()
        self.etl_pipeline = PipelineETL()
        self.valuation_engine = ValuationEngine()
        self.scoring_engine = ScoringEngine()
        self.selector = BestOpportunitySelector()
        self.formatter = MessageFormatter()
        self.bot = TelegramBot()
        self.repo = None  # Will be initialized when needed

    async def run_45min_scraping(self, scrape_minutes: int = 45):
        """Run continuous scraping for specified duration with partial ETL.

        Args:
            scrape_minutes: Duration of scraping phase (default: 45)
        """
        logger.info(f"Phase 1: Scraping for {scrape_minutes} minutes...")

        scrape_seconds = scrape_minutes * 60
        etl_interval = 5 * 60  # Partial ETL every 5 minutes
        last_etl_time = datetime.now()

        start_time = datetime.now()
        total_scraped = 0
        etl_count = 0

        while (datetime.now() - start_time).total_seconds() < scrape_seconds:
            try:
                # Scraping cycle
                async with JobLogger("scraping.cycle") as jl:
                    summary = await self.spider_manager.run_all_cycle(
                        active_portals=["imovirtual", "casa_sapo", "era", "remax"],
                    )
                    cycle_count = sum(summary.values()) if summary else 0
                    jl.records_processed = cycle_count
                    total_scraped += cycle_count
                    logger.info(f"Scraped {cycle_count} listings in this cycle (total: {total_scraped})")
            except Exception as e:
                logger.error(f"Scraping cycle failed: {e}")

            # Partial ETL every 5 minutes
            time_since_last_etl = (datetime.now() - last_etl_time).total_seconds()
            if time_since_last_etl >= etl_interval:
                logger.info("Running partial ETL...")
                try:
                    async with JobLogger("etl.partial") as jl:
                        etl_processed = await self.etl_pipeline.run(batch_size=5000)
                        jl.records_processed = etl_processed
                        etl_count += 1
                        logger.info(f"Partial ETL processed {etl_processed} listings (total partial ETLs: {etl_count})")
                except Exception as e:
                    logger.error(f"Partial ETL failed: {e}")
                last_etl_time = datetime.now()

            # Wait before next scraping cycle
            await asyncio.sleep(30)  # 30 seconds between cycles

        logger.info(f"Phase 1 complete: Scraped {total_scraped} listings in {scrape_minutes} minutes")
        logger.info(f"Partial ETLs run: {etl_count}")

    async def run_15min_analysis(self):
        """Run analysis phase: final ETL, valuation, scoring, selection, notification."""
        logger.info("Phase 2: Running analysis...")

        # Final ETL
        logger.info("Running final ETL...")
        try:
            async with JobLogger("etl.final") as jl:
                etl_count = await self.etl_pipeline.run(batch_size=10000)
                jl.records_processed = etl_count
            logger.info(f"Final ETL processed {etl_count} listings")
        except Exception as e:
            logger.error(f"Final ETL failed: {e}")
            return

        # Valuation
        logger.info("Running Valuation Engine...")
        try:
            async with JobLogger("valuation.batch") as jl:
                val_count = await self.valuation_engine.valuate_batch(batch_size=10000)
                jl.records_processed = val_count
            logger.info(f"Valuation processed {val_count} listings")
        except Exception as e:
            logger.error(f"Valuation failed: {e}")
            return

        # Scoring
        logger.info("Running Scoring Engine...")
        try:
            async with JobLogger("scoring.batch") as jl:
                score_count = await self.scoring_engine.score_batch(batch_size=10000)
                jl.records_processed = score_count
            logger.info(f"Scoring processed {score_count} listings")
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return

        # Selection of single best opportunity
        logger.info("Selecting single best opportunity...")
        try:
            best_opportunity = self.selector.select_single_best(min_score=7.0)

            if not best_opportunity:
                logger.info("No suitable opportunity found")
                return

            logger.info(
                f"Selected: {best_opportunity['listing'].titulo} "
                f"(score: {best_opportunity['score'].score_total:.1f}, "
                f"composite: {best_opportunity.get('composite_score', 'N/A')})"
            )
        except Exception as e:
            logger.error(f"Selection failed: {e}")
            return

        # Format message
        logger.info("Formatting message...")
        try:
            message = self.formatter.format_single_best_opportunity(best_opportunity)
            logger.info(f"Message length: {len(message)} characters")
        except Exception as e:
            logger.error(f"Message formatting failed: {e}")
            return

        # Send notification
        logger.info("Sending Telegram notification...")
        try:
            from realestate_engine.database.repository import DatabaseRepository
            if not self.repo:
                self.repo = DatabaseRepository()

            # Send message
            msg_id = await self.bot.send_message(message)

            if msg_id:
                logger.info(f"✅ Telegram message sent successfully (ID: {msg_id})")

                # Record notification in database
                notification = Notification(
                    id=str(__import__('uuid').uuid4()),
                    listing_id=best_opportunity["listing"].id,
                    message=message[:1000],  # Truncate for storage
                    status="sent",
                    sent_at=datetime.now(),
                )
                self.repo.create_notification(notification)
                logger.info("Notification recorded in database")
            else:
                logger.error("Failed to send Telegram message")
        except Exception as e:
            logger.error(f"Notification failed: {e}")

        logger.info("Phase 2 complete")

    async def run_cycle(self, scrape_minutes: int = 45):
        """Run a complete 60-minute cycle.

        Args:
            scrape_minutes: Duration of scraping phase (default: 45)
        """
        logger.info("=" * 60)
        logger.info(f"Starting 60-minute cycle (scraping: {scrape_minutes}min, analysis: 15min)")
        logger.info("=" * 60)

        try:
            # Phase 1: Scraping + Clean (45min)
            await self.run_45min_scraping(scrape_minutes=scrape_minutes)

            # Phase 2: Analysis (15min)
            await self.run_15min_analysis()

            logger.info("=" * 60)
            logger.info("60-minute cycle completed successfully")
            logger.info("=" * 60)

        except Exception as e:
            logger.exception(f"Cycle failed: {e}")

    async def run_once(self, scrape_minutes: int = 45):
        """Run a single cycle and exit.

        Args:
            scrape_minutes: Duration of scraping phase (default: 45)
        """
        await self.run_cycle(scrape_minutes=scrape_minutes)

    async def run_forever(self, interval_minutes: int = 60, scrape_minutes: int = 45):
        """Run cycles continuously forever.

        Args:
            interval_minutes: Total cycle duration (default: 60)
            scrape_minutes: Duration of scraping phase (default: 45)
        """
        logger.info(
            f"Starting Single Best Opportunity Scheduler "
            f"(cycle: {interval_minutes}min, scraping: {scrape_minutes}min, analysis: {interval_minutes - scrape_minutes}min)"
        )

        # Send startup notification
        try:
            startup_msg = (
                "🚀 *Real Estate Engine - Single Best Scheduler Started*\n\n"
                f"⏰ Iniciado às: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔄 Ciclo: {scrape_minutes}min scraping + {interval_minutes - scrape_minutes}min análise\n"
                f"🎯 Seleciona apenas 1 melhor oportunidade por ciclo\n"
                f"📱 Envia notificação Telegram completa com todos os detalhes\n\n"
                "A monitorizar mercado imobiliário do Porto..."
            )
            await self.bot.send_message(startup_msg)
            logger.info("Startup notification sent")
        except Exception as e:
            logger.warning(f"Could not send startup notification: {e}")

        while True:
            try:
                await self.run_cycle(scrape_minutes=scrape_minutes)
                logger.info(f"Waiting {interval_minutes} minutes before next cycle...")
                await asyncio.sleep(interval_minutes * 60)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutting down Single Best Opportunity Scheduler...")
                break
            except Exception as e:
                logger.error(f"Cycle failed, retrying in 5 minutes: {e}")
                await asyncio.sleep(300)


async def main():
    """Main entry point for testing."""
    scheduler = SingleBestOpportunityScheduler()

    # Run a single 5-minute scraping + 2-minute analysis cycle for testing
    await scheduler.run_once(scrape_minutes=5)


if __name__ == "__main__":
    asyncio.run(main())
