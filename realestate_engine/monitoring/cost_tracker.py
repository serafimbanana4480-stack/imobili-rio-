"""Cost and efficiency tracking for production readiness and ROI analysis."""
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class CostSnapshot:
    timestamp: str
    source: str
    event_type: str
    count: int
    estimated_cost_eur: float
    metadata: Dict


class CostTracker:
    def __init__(self, db_path: str = "data/db/cost_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                source TEXT,
                event_type TEXT,
                count INTEGER,
                estimated_cost_eur REAL,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record(self, source: str, event_type: str, count: int = 1, cost_per_unit: float = 0.0, metadata: Optional[Dict] = None):
        snapshot = CostSnapshot(
            timestamp=datetime.now(UTC).isoformat(),
            source=source,
            event_type=event_type,
            count=count,
            estimated_cost_eur=round(count * cost_per_unit, 4),
            metadata=metadata or {},
        )
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cost_snapshots (timestamp, source, event_type, count, estimated_cost_eur, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (snapshot.timestamp, snapshot.source, snapshot.event_type, snapshot.count, snapshot.estimated_cost_eur, json.dumps(snapshot.metadata)))
        conn.commit()
        conn.close()
        logger.info(f"CostTracker: {source}/{event_type} count={count} cost={snapshot.estimated_cost_eur} EUR")

    def get_summary(self, days: int = 30) -> Dict:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source, event_type, SUM(count), SUM(estimated_cost_eur)
            FROM cost_snapshots
            WHERE timestamp > datetime('now', ?)
            GROUP BY source, event_type
        """, (f"-{days} days",))
        rows = cursor.fetchall()
        conn.close()
        return {
            "period_days": days,
            "breakdown": [
                {"source": r[0], "event_type": r[1], "total_count": r[2], "total_cost_eur": round(r[3], 4)}
                for r in rows
            ],
            "total_cost_eur": round(sum(r[3] for r in rows), 4),
        }

    def get_cost_per_lead(self, days: int = 30) -> Optional[float]:
        summary = self.get_summary(days)
        total_cost = summary["total_cost_eur"]
        total_events = sum(b["total_count"] for b in summary["breakdown"])
        if total_events == 0:
            return None
        return round(total_cost / total_events, 4)
