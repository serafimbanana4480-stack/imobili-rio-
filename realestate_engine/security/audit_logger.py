"""Audit logging for security-sensitive operations.

Tracks who did what and when for compliance, forensics,
and security monitoring purposes.
"""
import json
import os
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from loguru import logger

UTC = timezone.utc


@dataclass
class AuditEntry:
    action: str
    actor: str = "system"
    resource: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    outcome: str = "success"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ip_address: str = ""
    session_id: str = ""


class AuditLogger:
    """Thread-safe audit trail logger."""

    _instance: Optional["AuditLogger"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.RLock()
        self._buffer: List[AuditEntry] = []
        self._buffer_size = 100
        self._log_dir = Path(os.getenv("REE_AUDIT_DIR", "logs/audit"))
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._current_log_file: Optional[str] = None
        self._rotate_log_file()
        self.total_entries = 0

    def _rotate_log_file(self):
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        self._current_log_file = str(self._log_dir / f"audit_{date_str}.jsonl")

    def log(self, action: str, actor: str = "system", resource: str = "",
            details: Optional[Dict] = None, outcome: str = "success",
            ip_address: str = "", session_id: str = ""):
        entry = AuditEntry(
            action=action,
            actor=actor,
            resource=resource,
            details=details or {},
            outcome=outcome,
            ip_address=ip_address,
            session_id=session_id,
        )

        with self._lock:
            self._buffer.append(entry)
            self.total_entries += 1

            if len(self._buffer) >= self._buffer_size:
                self._flush()

    def _flush(self):
        if not self._buffer:
            return

        self._rotate_log_file()
        try:
            with open(self._current_log_file, "a") as f:
                for entry in self._buffer:
                    f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
            count = len(self._buffer)
            self._buffer.clear()
            logger.debug(f"Flushed {count} audit entries to {self._current_log_file}")
        except Exception as e:
            logger.error(f"Failed to flush audit log: {e}")

    def flush(self):
        with self._lock:
            self._flush()

    def query(self, action: Optional[str] = None, actor: Optional[str] = None,
              limit: int = 100) -> List[Dict]:
        results = []
        self._flush()

        log_files = sorted(self._log_dir.glob("audit_*.jsonl"), reverse=True)
        for log_file in log_files:
            if len(results) >= limit:
                break
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        entry = json.loads(line)
                        if action and entry.get("action") != action:
                            continue
                        if actor and entry.get("actor") != actor:
                            continue
                        results.append(entry)
                        if len(results) >= limit:
                            break
            except Exception as e:
                logger.warning(f"Error reading audit log {log_file}: {e}")

        return results

    @property
    def stats(self) -> Dict:
        with self._lock:
            return {
                "total_entries": self.total_entries,
                "buffer_size": len(self._buffer),
                "log_dir": str(self._log_dir),
                "current_file": self._current_log_file,
            }


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(action: str, **kwargs):
    get_audit_logger().log(action, **kwargs)
