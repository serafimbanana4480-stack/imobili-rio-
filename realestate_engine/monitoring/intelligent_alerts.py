"""Intelligent alerting system with thresholds, anomaly detection and severity classification."""
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional
from statistics import mean, stdev

from loguru import logger


@dataclass
class AlertRule:
    name: str
    metric: str
    threshold: float
    operator: str
    severity: str
    cooldown_minutes: int
    enabled: bool = True


@dataclass
class AlertEvent:
    rule_name: str
    severity: str
    message: str
    metric_value: float
    threshold: float
    timestamp: str
    context: Dict = None


class IntelligentAlertEngine:
    def __init__(self, db_path: str = "data/db/intelligent_alerts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._load_default_rules()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT,
                severity TEXT,
                message TEXT,
                metric_value REAL,
                threshold REAL,
                timestamp TEXT,
                context TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                name TEXT PRIMARY KEY,
                metric TEXT,
                threshold REAL,
                operator TEXT,
                severity TEXT,
                cooldown_minutes INTEGER,
                enabled INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def _load_default_rules(self):
        defaults = [
            AlertRule("scraper_block_rate", "scraper.block_rate", 0.8, ">", "critical", 60),
            AlertRule("db_latency_high", "db.latency_ms", 1000, ">", "warning", 30),
            AlertRule("cache_hit_rate_low", "cache.hit_rate", 0.4, "<", "warning", 60),
            AlertRule("model_accuracy_drop", "model.accuracy", 0.7, "<", "critical", 120),
            AlertRule("listing_quality_drop", "quality.overall_score", 0.6, "<", "warning", 60),
        ]
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        for rule in defaults:
            cursor.execute("""
                INSERT OR IGNORE INTO alert_rules (name, metric, threshold, operator, severity, cooldown_minutes, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rule.name, rule.metric, rule.threshold, rule.operator, rule.severity, rule.cooldown_minutes, int(rule.enabled)))
        conn.commit()
        conn.close()

    def evaluate_rules(self, metrics: Dict[str, float]) -> List[AlertEvent]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alert_rules WHERE enabled = 1")
        rules = cursor.fetchall()
        conn.close()

        alerts = []
        for rule in rules:
            name, metric_key, threshold, operator, severity, cooldown, enabled = rule
            current_value = metrics.get(metric_key)
            if current_value is None:
                continue

            triggered = False
            if operator == ">" and current_value > threshold:
                triggered = True
            elif operator == "<" and current_value < threshold:
                triggered = True
            elif operator == "==" and current_value == threshold:
                triggered = True

            if triggered and not self._is_in_cooldown(name):
                alerts.append(AlertEvent(
                    rule_name=name,
                    severity=severity,
                    message=f"{metric_key}={current_value:.4f} triggered {operator} threshold={threshold}",
                    metric_value=current_value,
                    threshold=threshold,
                    timestamp=datetime.now(UTC).isoformat(),
                    context={"operator": operator, "metric": metric_key},
                ))

        if alerts:
            self._save_alerts(alerts)
        return alerts

    def _is_in_cooldown(self, rule_name: str) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM alert_events
            WHERE rule_name = ? ORDER BY timestamp DESC LIMIT 1
        """, (rule_name,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        last_alert = datetime.fromisoformat(row[0])
        conn2 = sqlite3.connect(str(self.db_path))
        try:
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT cooldown_minutes FROM alert_rules WHERE name = ?", (rule_name,))
            cooldown_row = cursor2.fetchone()
            cooldown_minutes = cooldown_row[0] if cooldown_row else 60
        finally:
            conn2.close()
        elapsed = (datetime.now(UTC) - last_alert).total_seconds() / 60
        return elapsed < cooldown_minutes

    def _save_alerts(self, alerts: List[AlertEvent]):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        for alert in alerts:
            cursor.execute("""
                INSERT INTO alert_events (rule_name, severity, message, metric_value, threshold, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.rule_name,
                alert.severity,
                alert.message,
                alert.metric_value,
                alert.threshold,
                alert.timestamp,
                json.dumps(alert.context or {}),
            ))
            logger.warning(f"INTELLIGENT_ALERT: {alert.rule_name} [{alert.severity}] {alert.message}")
        conn.commit()
        conn.close()

    def get_recent_alerts(self, severity: Optional[str] = None, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if severity:
            cursor.execute("""
                SELECT * FROM alert_events WHERE severity = ? ORDER BY timestamp DESC LIMIT ?
            """, (severity, limit))
        else:
            cursor.execute("""
                SELECT * FROM alert_events ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "rule_name": r[1],
                "severity": r[2],
                "message": r[3],
                "metric_value": r[4],
                "threshold": r[5],
                "timestamp": r[6],
                "context": json.loads(r[7]) if r[7] else {},
            }
            for r in rows
        ]
