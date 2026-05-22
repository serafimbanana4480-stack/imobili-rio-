"""System orchestrator.

Runs the real estate engine autonomously 24/7 using APScheduler.
Coordinates the scraping, ETL, valuation, scoring, and notification pipelines.
Respects night silence hours for Telegram notifications.

Hardening notes (Onda 4):
- ``max_instances=1`` + ``coalesce=True`` so a long-running pipeline (>1 h)
  never overlaps with itself and a pile of misfired triggers (e.g. laptop
  closed for 4 h) collapses into a single catch-up run.
- ``misfire_grace_time=1800`` tolerates up to 30 min of clock drift /
  suspend without losing the trigger entirely.
- APScheduler ``EVENT_JOB_*`` listener emits structured logs with duration
  so 24 h health can be inspected from ``logs/engine.log`` alone.
"""
import asyncio
import os
import time
from datetime import datetime
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import (
    EVENT_JOB_SUBMITTED,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    EVENT_JOB_MAX_INSTANCES,
)

from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.scraping.spider_config import SpiderConfig
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.notification.notification_engine import NotificationEngine
from realestate_engine.utils.job_logger import JobLogger


class Orchestrator:
    """Enterprise Scheduler for 24/7 Autonomous Operation."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.spider_manager = SpiderManager()
        self.etl_pipeline = PipelineETL()
        self.valuation_engine = ValuationEngine()
        self.scoring_engine = ScoringEngine()
        self.notifier = NotificationEngine()
        
        # Configuration
        self.silence_start_hour = 0   # 12 AM (midnight)
        self.silence_end_hour = 7     # 7 AM

    def _rapid_profile(self) -> SpiderConfig:
        """Small, fast scan that still covers every portal.

        Rapid mode should be selective in depth, not selective in portal
        coverage. We therefore keep the same portal universe but restrict each
        spider to only a couple of pages.
        """
        return SpiderConfig(max_pages=2, headless=True)

    def _full_profile(self) -> SpiderConfig:
        """Deeper scan for the full pipeline."""
        return SpiderConfig(max_pages=10, headless=True)

    def _engine_profile(self) -> SpiderConfig:
        """24h engine profile optimized for sustained operation."""
        return SpiderConfig(max_pages=6, headless=True)

    async def run_rapid_pipeline(self):
        """Intelligent rapid pipeline (~5-10 min)"""
        logger.info("Starting Intelligent Rapid Pipeline...")
        os.environ["ENRICH_SKIP_HEAVY"] = "1"
        os.environ["GEOCAPE_FORCE_FAST"] = "1" 
        
        try:
            # 1. Faster Scraping (limited pages)
            config = SpiderConfig(max_pages=2, concurrent_requests=10)
            listings = await self.spider_manager.run_all_spiders(config=config)
            
            if not listings:
                logger.warning("No listings found during rapid scan.")
                return

            # 2. Basic ETL & Deduplication
            cleaned = await self.etl_pipeline.process_batch(listings)
            
            # 3. High-Speed Valuation
            await self.valuation_engine.valuate_batch(cleaned)
            
            # 4. Light Scoring
            await self.scoring_engine.score_batch(cleaned)
            
            logger.info(f"Rapid pipeline completed. Processed {len(cleaned)} listings.")
        except Exception as e:
            logger.error(f"Rapid pipeline failed: {e}")

        if not self._is_silence_period():
            try:
                async with JobLogger("notification.top_opps") as jl:
                    sent = await self.notifier.notify_ai_analysis(limit=2)
                    jl.records_processed = int(sent or 0)
            except Exception as e:
                logger.exception(f"Rapid AI notification failed: {e}")
        
    def _is_silence_period(self) -> bool:
        """Check if current time is within the night silence window."""
        current_hour = datetime.now().hour
        if self.silence_start_hour < self.silence_end_hour:
            # Non-wrapping period (e.g., 0-7: midnight to 7 AM)
            return self.silence_start_hour <= current_hour < self.silence_end_hour
        else:
            # Wrapping period (e.g., 23-8: 11 PM to 8 AM next day)
            return current_hour >= self.silence_start_hour or current_hour < self.silence_end_hour

    async def run_full_pipeline(self):
        """Execute the full end-to-end real estate intelligence pipeline."""
        logger.info("Starting scheduled end-to-end pipeline execution.")
        
        try:
            # 1. Scrape (direct-fetch spiders: no browser, no proxy needed)
            try:
                async with JobLogger("scraping.cycle") as jl:
                    logger.info("Phase 1: Scraping active portals...")
                    summary = await self.spider_manager.run_all_cycle(
                        active_portals=self.spider_manager.DEFAULT_CYCLE_PORTALS,
                        config=self._full_profile(),
                    )
                    jl.records_processed = sum(summary.values()) if summary else 0
            except Exception as e:
                logger.exception(f"Phase 1 (Scraping) failed: {e}")

            # 2. ETL (includes deduplication and enrichment)
            try:
                async with JobLogger("etl.pipeline") as jl:
                    logger.info("Phase 2: Running ETL Pipeline...")
                    jl.records_processed = await self.etl_pipeline.run(batch_size=10000, force_full=True)
            except Exception as e:
                logger.exception(f"Phase 2 (ETL) failed: {e}")

            # 3. Valuation
            try:
                async with JobLogger("valuation.batch") as jl:
                    logger.info("Phase 3: Running Valuation Engine...")
                    jl.records_processed = await self.valuation_engine.valuate_batch(batch_size=10000)
            except Exception as e:
                logger.exception(f"Phase 3 (Valuation) failed: {e}")

            # 4. Scoring
            try:
                async with JobLogger("scoring.batch") as jl:
                    logger.info("Phase 4: Running Scoring Engine...")
                    jl.records_processed = await self.scoring_engine.score_batch(batch_size=10000)
            except Exception as e:
                logger.exception(f"Phase 4 (Scoring) failed: {e}")

            # 5. Notifications
            try:
                if self._is_silence_period():
                    logger.info("Phase 5: Notification skipped (Night Silence Period).")
                else:
                    async with JobLogger("notification.top_opps") as jl:
                        logger.info("Phase 5: Sending Telegram Notifications for top opportunities...")
                        sent = await self.notifier.notify_top_opportunities(min_score=9.0, max_notifications=3)
                        jl.records_processed = int(sent or 0)
            except Exception as e:
                logger.exception(f"Phase 5 (Notification) failed: {e}")

            # 6. AI Analysis (send detailed analysis of top deals)
            try:
                if self._is_silence_period():
                    logger.info("Phase 6: AI Analysis skipped (Night Silence Period).")
                else:
                    async with JobLogger("ai.analysis") as jl:
                        logger.info("Phase 6: Running AI Analysis and sending detailed notifications...")
                        sent = await self.notifier.notify_ai_analysis(limit=3)
                        jl.records_processed = int(sent or 0)
            except Exception as e:
                logger.exception(f"Phase 6 (AI Analysis) failed: {e}")
                
            logger.info("End-to-End pipeline execution completed successfully.")
            
        except Exception as e:
            logger.exception(f"Critical outer error during pipeline execution: {e}")

    async def send_daily_summary(self):
        """Send a daily market summary."""
        logger.info("Running daily summary job...")
        await self.notifier.send_daily_summary()

    def _on_scheduler_event(self, event) -> None:
        """Emit structured logs for every job lifecycle event.

        24 h reliability hinges on being able to grep `logs/engine.log` for
        ``apscheduler.event=`` and immediately see whether jobs ran, took
        too long, or were skipped because the previous run was still going.
        """
        job_id = getattr(event, "job_id", "unknown")
        if event.code == EVENT_JOB_EXECUTED:
            elapsed = self._job_started_at.pop(job_id, None)
            duration = (time.time() - elapsed) if elapsed else None
            logger.info(
                "apscheduler.event=executed job_id={} duration_s={:.1f}".format(
                    job_id, duration if duration is not None else -1.0
                )
            )
        elif event.code == EVENT_JOB_ERROR:
            elapsed = self._job_started_at.pop(job_id, None)
            duration = (time.time() - elapsed) if elapsed else None
            exc = getattr(event, "exception", None)
            logger.error(
                "apscheduler.event=error job_id={} duration_s={:.1f} exc={}".format(
                    job_id,
                    duration if duration is not None else -1.0,
                    f"{exc.__class__.__name__}: {exc}" if exc else "unknown",
                )
            )
        elif event.code == EVENT_JOB_MISSED:
            logger.warning(
                f"apscheduler.event=missed job_id={job_id} "
                f"scheduled_run_time={getattr(event, 'scheduled_run_time', '?')} "
                "(misfire_grace_time exceeded; tune misfire_grace_time if frequent)"
            )
        elif event.code == EVENT_JOB_MAX_INSTANCES:
            logger.warning(
                f"apscheduler.event=max_instances job_id={job_id} "
                "(previous run still in progress; this trigger was DROPPED — "
                "tune the trigger frequency or speed up the job)"
            )

    def start(self):
        """Start the scheduler with 24/7 hardened defaults."""
        self._job_started_at: dict[str, float] = {}

        # Run the full pipeline every hour from 8:00 to 22:00 (Lisbon time
        # interpreted as the host's local time — see _is_silence_period).
        # ``max_instances=1`` blocks overlap, ``coalesce=True`` collapses
        # missed triggers into one catch-up run, ``misfire_grace_time``
        # tolerates short clock drifts and laptop suspensions.
        self.scheduler.add_job(
            self.run_full_pipeline,
            CronTrigger(hour="8-22", minute="0"),
            id="full_pipeline",
            name="End-to-End Pipeline",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        # Send daily summary at 20:30 — same hardening, smaller grace window.
        self.scheduler.add_job(
            self.send_daily_summary,
            CronTrigger(hour="20", minute="30"),
            id="daily_summary",
            name="Daily Summary",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,
        )

        # Wire listeners BEFORE start() so the immediate boot cycle from
        # main_engine.py is already observable.
        self.scheduler.add_listener(self._track_job_start, EVENT_JOB_SUBMITTED)
        self.scheduler.add_listener(
            self._on_scheduler_event,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES,
        )

        logger.info(
            "Orchestrator started. 24/7 Scheduler is active. "
            "Jobs: full_pipeline (hourly 8-22), daily_summary (20:30). "
            "Hardening: max_instances=1, coalesce=True, misfire_grace_time={1800,600}."
        )
        self.scheduler.start()

    def _track_job_start(self, event) -> None:
        """Stamp job start time so ``_on_scheduler_event`` can compute duration.

        APScheduler emits ``EVENT_JOB_SUBMITTED`` the moment a job is handed
        to the executor — close enough to "start" for our purposes.
        """
        job_id = getattr(event, "job_id", "unknown")
        self._job_started_at[job_id] = time.time()
        logger.debug(f"apscheduler.event=submitted job_id={job_id}")

    async def run_forever(self):
        """Keep the orchestrator running in the main event loop."""
        self.start()

        # Send startup notification in background (don't block startup)
        asyncio.create_task(self._send_startup_notification_async())

        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down orchestrator...")
            self.scheduler.shutdown()

    async def _send_startup_notification_async(self):
        """Fire-and-forget startup notification with timeout."""
        try:
            await asyncio.wait_for(self.notifier.send_startup_message(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Startup notification timed out after 10s")
        except Exception as e:
            logger.warning(f"Could not send startup notification: {e}")
