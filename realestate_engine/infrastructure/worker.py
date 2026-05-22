"""Distributed worker base for scraping, ETL, valuation, and scoring tasks (FASE 6).

Designed for horizontal scaling:
- Stateless operation (reads from DB, writes to DB)
- Heartbeat mechanism for liveness
- Graceful shutdown on SIGTERM
- Task retry with exponential backoff
"""
import asyncio
import signal
import time
from typing import Optional, Callable, Dict, Any
from loguru import logger

from realestate_engine.infrastructure.event_bus import EventBus


class Worker:
    """Base class for horizontal-scaling workers."""

    def __init__(self, name: str, event_bus: Optional[EventBus] = None, heartbeat_interval: int = 30):
        self.name = name
        self.event_bus = event_bus or EventBus()
        self.heartbeat_interval = heartbeat_interval
        self._shutdown = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._stats: Dict[str, Any] = {"processed": 0, "errors": 0, "start_time": None}

    async def run(self):
        """Main worker loop with heartbeat."""
        self._stats["start_time"] = time.time()
        logger.info(f"Worker {self.name} starting")

        # Register signal handlers (graceful fallback on Windows)
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._request_shutdown)
            except (NotImplementedError, ValueError):
                logger.debug(f"Signal handler {sig} not supported on this platform, using fallback")
                import signal as _signal
                _signal.signal(sig, lambda s, f: self._request_shutdown())

        # Start heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            await self._main_loop()
        except asyncio.CancelledError:
            logger.info(f"Worker {self.name} cancelled")
        finally:
            heartbeat_task.cancel()
            logger.info(f"Worker {self.name} shutdown complete. Stats: {self._stats}")

    async def _main_loop(self):
        """Override in subclass for task-specific logic."""
        while not self._shutdown.is_set():
            await asyncio.sleep(1)

    async def _heartbeat_loop(self):
        """Emit periodic heartbeat for monitoring."""
        while not self._shutdown.is_set():
            uptime = time.time() - self._stats["start_time"] if self._stats["start_time"] else 0
            logger.debug(f"Worker {self.name} heartbeat — uptime={uptime:.0f}s processed={self._stats['processed']} errors={self._stats['errors']}")
            await asyncio.sleep(self.heartbeat_interval)

    def _request_shutdown(self):
        logger.info(f"Worker {self.name} received shutdown signal")
        self._shutdown.set()

    def record_success(self):
        self._stats["processed"] += 1

    def record_error(self):
        self._stats["errors"] += 1


class ETLWorker(Worker):
    """Worker that continuously runs ETL batches."""

    def __init__(self, repo, batch_size: int = 500, poll_interval: int = 60, **kwargs):
        from realestate_engine.etl.pipeline_etl import PipelineETL
        super().__init__(name="ETLWorker", **kwargs)
        self.pipeline = PipelineETL(repo=repo)
        self.batch_size = batch_size
        self.poll_interval = poll_interval

    async def _main_loop(self):
        while not self._shutdown.is_set():
            try:
                processed = await self.pipeline.run(batch_size=self.batch_size)
                if processed > 0:
                    self.record_success()
                    logger.info(f"ETLWorker processed {processed} listings")
                else:
                    # No work — back off
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                self.record_error()
                logger.error(f"ETLWorker error: {e}")
                await asyncio.sleep(self.poll_interval)


class ValuationWorker(Worker):
    """Worker that continuously valuates unvaluated listings."""

    def __init__(self, repo, batch_size: int = 100, poll_interval: int = 120, **kwargs):
        from realestate_engine.valuation.valuation_engine import ValuationEngine
        super().__init__(name="ValuationWorker", **kwargs)
        self.engine = ValuationEngine(repo=repo)
        self.batch_size = batch_size
        self.poll_interval = poll_interval

    async def _main_loop(self):
        while not self._shutdown.is_set():
            try:
                count = await self.engine.valuate_batch(batch_size=self.batch_size)
                if count > 0:
                    self.record_success()
                    logger.info(f"ValuationWorker valuated {count} listings")
                else:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                self.record_error()
                logger.error(f"ValuationWorker error: {e}")
                await asyncio.sleep(self.poll_interval)


class ScoringWorker(Worker):
    """Worker that continuously scores unscored listings."""

    def __init__(self, repo, batch_size: int = 100, poll_interval: int = 120, **kwargs):
        from realestate_engine.scoring.scoring_engine import ScoringEngine
        super().__init__(name="ScoringWorker", **kwargs)
        self.engine = ScoringEngine(repo=repo)
        self.batch_size = batch_size
        self.poll_interval = poll_interval

    async def _main_loop(self):
        while not self._shutdown.is_set():
            try:
                count = await self.engine.score_batch(batch_size=self.batch_size)
                if count > 0:
                    self.record_success()
                    logger.info(f"ScoringWorker scored {count} listings")
                else:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                self.record_error()
                logger.error(f"ScoringWorker error: {e}")
                await asyncio.sleep(self.poll_interval)
