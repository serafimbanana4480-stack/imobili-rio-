"""Model monitoring with drift detection persistence."""
import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional
from statistics import mean, stdev

from loguru import logger


@dataclass
class ModelPerformanceSnapshot:
    model_name: str
    version: str
    timestamp: str
    r_squared: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    sample_size: int = 0
    feature_stats: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class DriftAlert:
    model_name: str
    feature: str
    baseline_mean: float
    current_mean: float
    shift_percent: float
    severity: str
    timestamp: str


class ModelMonitor:
    def __init__(self, db_path: str = "data/db/model_monitor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                version TEXT,
                timestamp TEXT,
                r_squared REAL,
                mae REAL,
                rmse REAL,
                sample_size INTEGER,
                feature_stats TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                feature TEXT,
                baseline_mean REAL,
                current_mean REAL,
                shift_percent REAL,
                severity TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_snapshot(self, snapshot: ModelPerformanceSnapshot):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_snapshots
            (model_name, version, timestamp, r_squared, mae, rmse, sample_size, feature_stats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.model_name,
            snapshot.version,
            snapshot.timestamp,
            snapshot.r_squared,
            snapshot.mae,
            snapshot.rmse,
            snapshot.sample_size,
            json.dumps(snapshot.feature_stats),
        ))
        conn.commit()
        conn.close()
        logger.info(f"ModelMonitor: recorded snapshot for {snapshot.model_name} v{snapshot.version}")

    def detect_drift(
        self,
        model_name: str,
        current_stats: Dict[str, Dict],
        baseline_stats: Optional[Dict[str, Dict]] = None,
        threshold_percent: float = 20.0,
    ) -> List[DriftAlert]:
        alerts = []
        if baseline_stats is None:
            baseline_stats = self._get_latest_baseline(model_name)
        if not baseline_stats:
            logger.info(f"ModelMonitor: no baseline for {model_name}, establishing now")
            return alerts

        for feature, current in current_stats.items():
            base = baseline_stats.get(feature)
            if not base or base.get("mean", 0) == 0:
                continue
            current_mean = current.get("mean", 0)
            baseline_mean = base.get("mean", 1)
            shift = abs(current_mean - baseline_mean) / abs(baseline_mean) * 100
            if shift > threshold_percent:
                severity = "critical" if shift > 50 else "warning" if shift > 30 else "info"
                alerts.append(DriftAlert(
                    model_name=model_name,
                    feature=feature,
                    baseline_mean=baseline_mean,
                    current_mean=current_mean,
                    shift_percent=round(shift, 2),
                    severity=severity,
                    timestamp=datetime.now(UTC).isoformat(),
                ))
        return alerts

    def save_alerts(self, alerts: List[DriftAlert]):
        if not alerts:
            return
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        for alert in alerts:
            cursor.execute("""
                INSERT INTO drift_alerts
                (model_name, feature, baseline_mean, current_mean, shift_percent, severity, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.model_name,
                alert.feature,
                alert.baseline_mean,
                alert.current_mean,
                alert.shift_percent,
                alert.severity,
                alert.timestamp,
            ))
        conn.commit()
        conn.close()
        logger.warning(f"ModelMonitor: saved {len(alerts)} drift alerts")

    def _get_latest_baseline(self, model_name: str) -> Dict[str, Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT feature_stats FROM performance_snapshots
            WHERE model_name = ? ORDER BY timestamp DESC LIMIT 1
        """, (model_name,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return {}

    def get_recent_alerts(self, model_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if model_name:
            cursor.execute("""
                SELECT * FROM drift_alerts WHERE model_name = ? ORDER BY timestamp DESC LIMIT ?
            """, (model_name, limit))
        else:
            cursor.execute("""
                SELECT * FROM drift_alerts ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "model_name": r[1],
                "feature": r[2],
                "baseline_mean": r[3],
                "current_mean": r[4],
                "shift_percent": r[5],
                "severity": r[6],
                "timestamp": r[7],
            }
            for r in rows
        ]
