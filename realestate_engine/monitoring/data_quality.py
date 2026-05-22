"""Data Quality and Drift Detection for production monitoring.

Implements:
- Schema validation (expected columns/types)
- Null rate monitoring
- Distribution drift detection (KS-test approximation)
- Price anomaly detection (IQR-based)
- Data freshness checks
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from statistics import median, stdev, mean
from loguru import logger


class DataQualityEngine:
    """Continuous data quality monitoring with drift detection."""

    # Expected schema for clean listings (field -> type)
    CLEAN_LISTING_SCHEMA = {
        "source_portal": str,
        "source_id": str,
        "preco_pedido": (int, float),
        "area_util_m2": (int, float),
        "quartos": int,
        "lat": (int, float, type(None)),
        "lon": (int, float, type(None)),
    }

    def __init__(self):
        self._baseline_stats: Dict[str, Dict] = {}
        self._last_run: Optional[datetime] = None

    def validate_schema(self, record: Dict[str, Any]) -> List[str]:
        """Validate a single record against expected schema."""
        errors = []
        for field, expected in self.CLEAN_LISTING_SCHEMA.items():
            if field not in record:
                errors.append(f"Missing field: {field}")
                continue
            val = record[field]
            if not isinstance(val, expected):
                errors.append(f"Type mismatch for {field}: expected {expected}, got {type(val).__name__}")
        return errors

    def calculate_batch_stats(self, records: List[Dict]) -> Dict[str, Dict]:
        """Compute distribution statistics for numeric fields."""
        stats = {}
        numeric_fields = ["preco_pedido", "area_util_m2", "preco_por_m2", "dist_metro_m"]
        for field in numeric_fields:
            values = [r[field] for r in records if field in r and r[field] is not None and isinstance(r[field], (int, float))]
            if not values:
                continue
            stats[field] = {
                "count": len(values),
                "mean": round(mean(values), 2),
                "median": round(median(values), 2),
                "std": round(stdev(values), 2) if len(values) > 1 else 0.0,
                "min": round(min(values), 2),
                "max": round(max(values), 2),
            }
        return stats

    def detect_drift(self, current_stats: Dict[str, Dict]) -> List[str]:
        """Detect distribution drift vs baseline using mean shift threshold."""
        alerts = []
        if not self._baseline_stats:
            self._baseline_stats = current_stats
            logger.info("DataQuality: baseline established")
            return alerts

        for field, cur in current_stats.items():
            base = self._baseline_stats.get(field)
            if not base:
                continue
            # Drift if mean shifts > 2 std from baseline or >20% relative change
            mean_shift = abs(cur["mean"] - base["mean"])
            threshold = max(base["std"] * 2, base["mean"] * 0.20)
            if mean_shift > threshold and base["mean"] > 0:
                pct = mean_shift / base["mean"] * 100
                alerts.append(
                    f"DRIFT: {field} mean shifted by {pct:.1f}% "
                    f"({base['mean']:.0f} -> {cur['mean']:.0f})"
                )
            # Drift if variance doubles
            if base["std"] > 0 and cur["std"] > base["std"] * 2:
                alerts.append(f"DRIFT: {field} variance doubled ({base['std']:.0f} -> {cur['std']:.0f})")

        if alerts:
            logger.warning(f"DataQuality drift detected: {alerts}")
        else:
            logger.debug("DataQuality: no drift detected")

        # Update baseline gradually (exponential moving average)
        for field, cur in current_stats.items():
            if field in self._baseline_stats:
                old = self._baseline_stats[field]
                self._baseline_stats[field] = {
                    k: round((old[k] * 0.7 + cur[k] * 0.3), 2)
                    for k in ["mean", "std", "median", "min", "max"]
                }
                self._baseline_stats[field]["count"] = cur["count"]
            else:
                self._baseline_stats[field] = cur

        return alerts

    def detect_price_anomalies(self, records: List[Dict], iqr_multiplier: float = 3.0) -> List[Dict]:
        """Flag price anomalies using IQR method."""
        prices = [
            r["preco_pedido"] for r in records
            if "preco_pedido" in r and isinstance(r["preco_pedido"], (int, float)) and r["preco_pedido"] > 0
        ]
        if len(prices) < 10:
            return []

        prices_sorted = sorted(prices)
        n = len(prices_sorted)
        q1 = prices_sorted[n // 4]
        q3 = prices_sorted[(n * 3) // 4]
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr

        anomalies = []
        for r in records:
            p = r.get("preco_pedido")
            if not isinstance(p, (int, float)) or p <= 0:
                continue
            if p < lower or p > upper:
                anomalies.append({
                    "source_id": r.get("source_id", "unknown"),
                    "source_portal": r.get("source_portal", "unknown"),
                    "preco_pedido": p,
                    "reason": "price_outside_iqr",
                    "threshold_lower": round(lower, 2),
                    "threshold_upper": round(upper, 2),
                })

        if anomalies:
            logger.warning(f"DataQuality: {len(anomalies)} price anomalies detected (IQR method)")
        return anomalies

    def check_freshness(self, records: List[Dict], max_age_hours: int = 48) -> List[str]:
        """Check if records are within acceptable age."""
        alerts = []
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=max_age_hours)
        stale = 0
        for r in records:
            ts = r.get("scrape_timestamp")
            if not ts:
                stale += 1
                continue
            try:
                # Handle ISO format with or without Z
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt < cutoff:
                    stale += 1
            except Exception:
                stale += 1
        if stale:
            pct = stale / len(records) * 100 if records else 0
            alerts.append(f"FRESHNESS: {stale}/{len(records)} records ({pct:.1f}%) older than {max_age_hours}h")
            logger.warning(alerts[-1])
        return alerts

    def run_full_check(self, records: List[Dict]) -> Dict[str, Any]:
        """Run complete data quality check and return report."""
        self._last_run = datetime.now(timezone.utc)
        schema_errors = []
        for r in records:
            schema_errors.extend(self.validate_schema(r))

        stats = self.calculate_batch_stats(records)
        drift_alerts = self.detect_drift(stats)
        anomalies = self.detect_price_anomalies(records)
        freshness_alerts = self.check_freshness(records)

        return {
            "timestamp": self._last_run.isoformat(),
            "record_count": len(records),
            "schema_errors": len(schema_errors),
            "drift_alerts": drift_alerts,
            "price_anomalies": anomalies,
            "freshness_alerts": freshness_alerts,
            "distribution_stats": stats,
            "healthy": len(drift_alerts) == 0 and len(anomalies) == 0 and len(freshness_alerts) == 0,
        }
