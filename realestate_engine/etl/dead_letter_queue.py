"""Dead Letter Queue for failed ETL records.

Captures and persists failed records from ETL pipeline for investigation and retry.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from loguru import logger

from realestate_engine.database.repository import DatabaseRepository


class FailureReason(Enum):
    """Reasons for ETL record failure."""
    NORMALIZATION_ERROR = "normalization_error"
    DEDUPLICATION_ERROR = "deduplication_error"
    GEOCODING_ERROR = "geocoding_error"
    ENRICHMENT_ERROR = "enrichment_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    PYDANTIC_VALIDATION_ERROR = "pydantic_validation_error"


@dataclass
class FailedRecord:
    """Record that failed during ETL processing."""
    source_portal: str
    source_id: str
    raw_data: Dict[str, Any]
    stage: str  # normalization, deduplication, geocoding, enrichment, validation, database
    failure_reason: FailureReason
    error_message: str
    error_details: Optional[str] = None
    timestamp: Optional[datetime] = None
    retry_count: int = 0
    resolved: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DeadLetterQueue:
    """Dead letter queue for failed ETL records."""

    def __init__(self, repository: DatabaseRepository):
        self.repo = repository

    def add(self, failed_record: FailedRecord) -> Optional[int]:
        """Add failed record to DLQ.

        Returns the record ID if successful, None otherwise.
        """
        logger.warning(
            f"Adding to DLQ: {failed_record.source_portal}/{failed_record.source_id} "
            f"at stage {failed_record.stage}: {failed_record.failure_reason.value} - {failed_record.error_message}"
        )
        try:
            # Store in database
            record_id = self.repo.create_failed_record(
                source_portal=failed_record.source_portal,
                source_id=failed_record.source_id,
                raw_data=failed_record.raw_data,
                stage=failed_record.stage,
                failure_reason=failed_record.failure_reason.value,
                error_message=failed_record.error_message,
                error_details=failed_record.error_details,
                retry_count=failed_record.retry_count,
                resolved=failed_record.resolved
            )
            return record_id
        except Exception as e:
            logger.error(f"Failed to add record to DLQ: {e}")
            return None

    def get_unresolved(self, limit: int = 100) -> list:
        """Get unresolved failed records."""
        try:
            return self.repo.get_failed_records(resolved=False, limit=limit)
        except AttributeError:
            logger.warning("Repository does not support get_failed_records method")
            return []

    def mark_resolved(self, record_id: int):
        """Mark failed record as resolved."""
        try:
            self.repo.update_failed_record(record_id, resolved=True)
            logger.info(f"Marked failed record {record_id} as resolved")
        except AttributeError:
            logger.warning("Repository does not support update_failed_record method")

    def retry_record(self, failed_record: dict, pipeline) -> bool:
        """Retry processing a failed record.

        This is a placeholder for future implementation of retry logic.
        Currently, it just marks the record as attempted.
        """
        logger.info(f"Retry not yet implemented for {failed_record.get('source_id')}")
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        try:
            total = self.repo.count_failed_records()
            unresolved = self.repo.count_failed_records(resolved=False)
            by_reason = self.repo.count_failed_records_by_reason()
            by_stage = self.repo.count_failed_records_by_stage()
        except AttributeError:
            logger.warning("Repository does not support DLQ statistics methods")
            return {
                "total_failed": 0,
                "unresolved": 0,
                "resolved": 0,
                "by_reason": {},
                "by_stage": {}
            }

        return {
            "total_failed": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_reason": by_reason,
            "by_stage": by_stage
        }

    def cleanup_old_records(self, days: int = 30):
        """Clean up old resolved records."""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 86400)
            deleted = self.repo.delete_old_failed_records(cutoff_date)
            logger.info(f"Cleaned up {deleted} old DLQ records older than {days} days")
            return deleted
        except AttributeError:
            logger.warning("Repository does not support delete_old_failed_records method")
            return 0
