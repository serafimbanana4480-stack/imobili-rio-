"""Prometheus-compatible metrics exporter for real-time observability (FASE 7).

Exposes:
- scrape_listings_total (counter)
- etl_processed_total (counter)
- etl_errors_total (counter)
- etl_duration_seconds (histogram)
- valuation_computed_total (counter)
- scoring_computed_total (counter)
- data_quality_drift_detected (counter)
- proxy_health_score (gauge)
- active_workers (gauge)
"""
from typing import Dict, Any
from loguru import logger


class PrometheusExporter:
    """Simple Prometheus text-format exporter (no prometheus_client dependency)."""

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}

    def inc(self, metric: str, value: int = 1, labels: Dict[str, str] = None):
        key = self._key(metric, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def set_gauge(self, metric: str, value: float, labels: Dict[str, str] = None):
        key = self._key(metric, labels)
        self._gauges[key] = value

    def observe(self, metric: str, value: float, labels: Dict[str, str] = None):
        key = self._key(metric, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def _key(self, metric: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return metric
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f'{metric}{{{label_str}}}'

    def render(self) -> str:
        """Render current metrics in Prometheus text format."""
        lines = []
        # Counters
        for key, val in sorted(self._counters.items()):
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {val}")
        # Gauges
        for key, val in sorted(self._gauges.items()):
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {val}")
        # Histograms (render as sum and count)
        for key, vals in sorted(self._histograms.items()):
            base = key.split('{')[0]
            lines.append(f"# TYPE {base}_sum gauge")
            lines.append(f"{base}_sum{key[len(base):]} {sum(vals):.4f}")
            lines.append(f"# TYPE {base}_count counter")
            lines.append(f"{base}_count{key[len(base):]} {len(vals)}")
        return "\n".join(lines) + "\n"

    def get_http_response(self) -> str:
        return self.render()


# Global singleton for the application
_global_exporter: PrometheusExporter = None


def get_exporter() -> PrometheusExporter:
    global _global_exporter
    if _global_exporter is None:
        _global_exporter = PrometheusExporter()
    return _global_exporter
