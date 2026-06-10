"""Context manager that writes every pipeline job run into job_execution_log.

Usage:
    async with JobLogger("etl.pipeline") as jl:
        count = await etl.run()
        jl.records_processed = count
"""
from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from datetime import datetime, UTC
from typing import Optional

from loguru import logger

from realestate_engine.database.models import JobExecutionLog
from realestate_engine.database.repository import DatabaseRepository, transaction_scope


class JobLogger(AbstractAsyncContextManager, AbstractContextManager):
    """Writes a start/end row to job_execution_log for every pipeline phase.

    Works as both a sync and async context manager so it can wrap any
    orchestrator step without requiring call-site changes.
    """

    def __init__(self, job_name: str, repo: Optional[DatabaseRepository] = None):
        self.job_name = job_name
        self.repo = repo or DatabaseRepository()
        self.records_processed: int = 0
        self._row_id: Optional[int] = None
        self._started_at: Optional[datetime] = None

    # ── Sync enter/exit ────────────────────────────────────────────────
    def __enter__(self) -> "JobLogger":
        self._started_at = datetime.now(UTC)
        row = JobExecutionLog(
            job_name=self.job_name,
            started_at=self._started_at,
            status="running",
            records_processed=0,
        )
        with transaction_scope(self.repo.Session()) as session:
            session.add(row)
            session.flush()
            self._row_id = row.id
        logger.info(f"[job:{self.job_name}] started (id={self._row_id})")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._finalize(exc_type, exc)
        return False  # never swallow exceptions

    # ── Async enter/exit (just delegates) ──────────────────────────────
    async def __aenter__(self) -> "JobLogger":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        self._finalize(exc_type, exc)
        return False

    # ── internals ──────────────────────────────────────────────────────
    def _finalize(self, exc_type, exc):
        finished_at = datetime.now(UTC)
        status = "success" if exc is None else "failed"
        error_message = None if exc is None else f"{exc_type.__name__}: {exc}"

        try:
            with transaction_scope(self.repo.Session()) as session:
                row = session.get(JobExecutionLog, self._row_id)
                if row is None:
                    logger.warning(f"[job:{self.job_name}] log row {self._row_id} missing")
                    return
                row.finished_at = finished_at
                row.status = status
                row.error_message = error_message
                row.records_processed = int(self.records_processed or 0)
        except Exception as e:  # pragma: no cover — we must never hide the real exc
            logger.error(f"[job:{self.job_name}] failed to persist end-row: {e}")

        duration_s = (finished_at - (self._started_at or finished_at)).total_seconds()
        logger.info(
            f"[job:{self.job_name}] finished status={status} "
            f"records={self.records_processed} duration_s={duration_s:.2f}"
        )
