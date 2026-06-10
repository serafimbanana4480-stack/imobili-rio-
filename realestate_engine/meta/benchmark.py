"""Lightweight benchmarking harness for continuous performance tracking."""
import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Callable, Dict, List, Optional

from loguru import logger


@dataclass
class BenchmarkResult:
    name: str
    timestamp: str
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class BenchmarkEngine:
    def __init__(self, db_path: str = "data/db/benchmarks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                timestamp TEXT,
                duration_ms REAL,
                success INTEGER,
                error TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def run(self, name: str, fn: Callable, *args, **kwargs) -> BenchmarkResult:
        start = time.perf_counter()
        error = None
        success = False
        try:
            result = fn(*args, **kwargs)
            success = True
            metadata = {"result_type": type(result).__name__}
        except Exception as e:
            error = str(e)
            metadata = {"error_type": type(e).__name__}
            logger.warning(f"Benchmark {name} failed: {e}")
        duration_ms = (time.perf_counter() - start) * 1000

        bench = BenchmarkResult(
            name=name,
            timestamp=datetime.now(UTC).isoformat(),
            duration_ms=round(duration_ms, 2),
            success=success,
            error=error,
            metadata=metadata,
        )
        self._save(bench)
        return bench

    def _save(self, bench: BenchmarkResult):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO benchmark_results (name, timestamp, duration_ms, success, error, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bench.name, bench.timestamp, bench.duration_ms, int(bench.success), bench.error, json.dumps(bench.metadata)))
        conn.commit()
        conn.close()

    def get_history(self, name: str, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, timestamp, duration_ms, success, error, metadata
            FROM benchmark_results WHERE name = ? ORDER BY timestamp DESC LIMIT ?
        """, (name, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "name": r[0],
                "timestamp": r[1],
                "duration_ms": r[2],
                "success": bool(r[3]),
                "error": r[4],
                "metadata": json.loads(r[5]) if r[5] else {},
            }
            for r in rows
        ]

    def get_summary(self, name: str) -> Dict:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), AVG(duration_ms), MIN(duration_ms), MAX(duration_ms), SUM(success)
            FROM benchmark_results WHERE name = ?
        """, (name,))
        row = cursor.fetchone()
        conn.close()
        if not row or row[0] == 0:
            return {}
        total, avg, min_d, max_d, successes = row
        return {
            "total_runs": total,
            "avg_duration_ms": round(avg, 2) if avg else 0,
            "min_duration_ms": round(min_d, 2) if min_d else 0,
            "max_duration_ms": round(max_d, 2) if max_d else 0,
            "success_rate": round(successes / total * 100, 2) if total else 0,
        }
