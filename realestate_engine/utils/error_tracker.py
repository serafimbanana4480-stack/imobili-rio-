"""Error tracking and alerting utilities."""
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from loguru import logger
from realestate_engine.monitoring.metrics import MetricsCollector
import pytz

UTC = pytz.utc


class ErrorTracker:
    """Track and aggregate errors for monitoring and alerting."""

    def __init__(self, max_age_minutes: int = 60):
        self.max_age = timedelta(minutes=max_age_minutes)
        self.errors: Dict[str, List[Dict]] = defaultdict(list)
        self.metrics = MetricsCollector()

    def record_error(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict] = None,
        severity: str = "error"
    ):
        """Record an error occurrence."""
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "context": context or {},
            "severity": severity
        }
        
        self.errors[error_type].append(error_entry)
        
        # Record in metrics
        self.metrics.record_error(error_type)
        
        # Log
        log_func = logger.error if severity == "error" else logger.warning
        log_func(f"[{error_type}] {message}", extra={"context": context})

    def get_error_count(self, error_type: str, since_minutes: int = 5) -> int:
        """Get error count for a type in recent time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        
        count = 0
        for entry in self.errors.get(error_type, []):
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff:
                count += 1
        
        return count

    def get_error_summary(self, since_minutes: int = 5) -> Dict[str, int]:
        """Get summary of all errors in recent time window."""
        summary = {}
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        
        for error_type, entries in self.errors.items():
            count = 0
            for entry in entries:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff:
                    count += 1
            if count > 0:
                summary[error_type] = count
        
        return summary

    def cleanup_old_errors(self):
        """Remove errors older than max_age."""
        cutoff = datetime.utcnow() - self.max_age
        
        for error_type in list(self.errors.keys()):
            self.errors[error_type] = [
                entry for entry in self.errors[error_type]
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff
            ]
            
            if not self.errors[error_type]:
                del self.errors[error_type]

    def get_recent_errors(
        self,
        error_type: Optional[str] = None,
        limit: int = 10,
        since_minutes: int = 5
    ) -> List[Dict]:
        """Get recent errors, optionally filtered by type."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        
        all_errors = []
        error_types = [error_type] if error_type else self.errors.keys()
        
        for etype in error_types:
            for entry in self.errors.get(etype, []):
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff:
                    all_errors.append({**entry, "error_type": etype})
        
        # Sort by timestamp descending
        all_errors.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return all_errors[:limit]

    def should_alert(
        self,
        error_type: str,
        threshold: int = 5,
        window_minutes: int = 5
    ) -> bool:
        """Check if error rate exceeds threshold for alerting."""
        return self.get_error_count(error_type, window_minutes) >= threshold

    def get_error_rate(self, error_type: str, window_minutes: int = 5) -> float:
        """Get errors per minute for a type."""
        count = self.get_error_count(error_type, window_minutes)
        return count / window_minutes if window_minutes > 0 else 0


class ErrorAggregator:
    """Aggregate errors across multiple components."""

    def __init__(self):
        self.trackers: Dict[str, ErrorTracker] = {}

    def get_tracker(self, component: str) -> ErrorTracker:
        """Get or create error tracker for a component."""
        if component not in self.trackers:
            self.trackers[component] = ErrorTracker()
        return self.trackers[component]

    def record_error(
        self,
        component: str,
        error_type: str,
        message: str,
        context: Optional[Dict] = None,
        severity: str = "error"
    ):
        """Record error for a specific component."""
        tracker = self.get_tracker(component)
        tracker.record_error(error_type, message, context, severity)

    def get_global_summary(self, since_minutes: int = 5) -> Dict[str, Dict]:
        """Get error summary across all components."""
        global_summary = {}
        
        for component, tracker in self.trackers.items():
            summary = tracker.get_error_summary(since_minutes)
            if summary:
                global_summary[component] = summary
        
        return global_summary

    def cleanup_all(self):
        """Cleanup old errors across all trackers."""
        for tracker in self.trackers.values():
            tracker.cleanup_old_errors()


# Global error aggregator instance
error_aggregator = ErrorAggregator()
