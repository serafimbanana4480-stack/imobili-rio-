"""Metrics collection for Real Estate Opportunity Engine.

Enhanced with:
- Business metrics (opportunities found, market insights)
- Performance profiling
- Alerting thresholds
- Custom dashboards support
- Streamlit hot-reload safe (unregisters stale collectors before re-registering)
"""
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from datetime import datetime, timezone
from prometheus_client import Counter, Histogram, Gauge, start_http_server, Info, REGISTRY
from loguru import logger

from realestate_engine.utils.config import config

UTC = timezone.utc


class MetricsCollector:
    """Collects and exposes Prometheus metrics (Singleton).

    Streamlit hot-reload safe: when the class is re-defined after a reload,
    _instance is None but the global CollectorRegistry still holds the old
    metrics.  Before registering any metric we unregister any existing
    collector with the same name so that re-registration never raises
    ``ValueError: Duplicated timeseries``.
    """

    _instance = None

    # All metric names used by this class — used for bulk cleanup on reload.
    _METRIC_NAMES = [
        'realestate_jobs_total',
        'realestate_jobs_created',
        'realestate_jobs',
        'realestate_job_duration_seconds',
        'realestate_job_duration_seconds_created',
        'realestate_job_duration_seconds_bucket',
        'realestate_job_duration_seconds_sum',
        'realestate_job_duration_seconds_count',
        'realestate_listings_scraped_total',
        'realestate_listings_scraped_created',
        'realestate_listings_scraped',
        'realestate_listings_processed_total',
        'realestate_listings_processed_created',
        'realestate_listings_processed',
        'realestate_valuations_computed_total',
        'realestate_valuations_computed_created',
        'realestate_valuations_computed',
        'realestate_scores_computed_total',
        'realestate_scores_computed_created',
        'realestate_scores_computed',
        'realestate_notifications_sent_total',
        'realestate_notifications_sent_created',
        'realestate_notifications_sent',
        'realestate_model_accuracy',
        'realestate_model_accuracy_info',
        'realestate_model_drift_score',
        'realestate_model_drift_score_info',
        'realestate_db_connections_active',
        'realestate_db_connections_active_info',
        'realestate_pipeline_latency_seconds',
        'realestate_pipeline_latency_seconds_created',
        'realestate_pipeline_latency_seconds_bucket',
        'realestate_pipeline_latency_seconds_sum',
        'realestate_pipeline_latency_seconds_count',
        'realestate_opportunities_found_total',
        'realestate_opportunities_found_created',
        'realestate_opportunities_found',
        'realestate_avg_discount_percent',
        'realestate_avg_discount_percent_info',
        'realestate_market_price_trend',
        'realestate_market_price_trend_info',
        'realestate_active_listings_count',
        'realestate_active_listings_count_info',
        'realestate_high_score_listings',
        'realestate_high_score_listings_info',
        'realestate_api_request_duration_seconds',
        'realestate_api_request_duration_seconds_created',
        'realestate_api_request_duration_seconds_bucket',
        'realestate_api_request_duration_seconds_sum',
        'realestate_api_request_duration_seconds_count',
        'realestate_cache_hit_rate',
        'realestate_cache_hit_rate_info',
        'realestate_memory_usage_bytes',
        'realestate_memory_usage_bytes_info',
        'realestate_system_info',
        'realestate_system_info_info',
        'realestate_alerts_triggered_total',
        'realestate_alerts_triggered_created',
        'realestate_alerts_triggered',
        'realestate_data_quality_score',
        'realestate_data_quality_score_info',
        'realestate_data_quality_completeness',
        'realestate_data_quality_completeness_info',
        'realestate_data_quality_accuracy',
        'realestate_data_quality_accuracy_info',
    ]

    @classmethod
    def _unregister_stale_metrics(cls):
        """Remove any previously registered realestate_* collectors.

        This is necessary because Streamlit hot-reloads re-define the
        MetricsCollector class (resetting _instance to None) while the
        prometheus_client CollectorRegistry persists across reloads.
        Without cleanup, re-registering raises Duplicated timeseries.
        """
        # Collect collectors to remove first (avoid mutating dict during iteration)
        to_remove = []
        for name in list(REGISTRY._names_to_collectors.keys()):
            if name.startswith('realestate_'):
                to_remove.append(REGISTRY._names_to_collectors[name])
        for collector in to_remove:
            try:
                REGISTRY.unregister(collector)
            except (KeyError, ValueError):
                pass

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, port: Optional[int] = None):
        if self._initialized:
            return

        # Clean up any stale collectors from a previous Streamlit hot-reload
        self._unregister_stale_metrics()

        self.port = port or config.prometheus_port
        self._started = False

        # Prometheus metrics
        self.jobs_total = Counter(
            'realestate_jobs_total',
            'Total jobs executed',
            ['job_name', 'status']
        )
        self.job_duration = Histogram(
            'realestate_job_duration_seconds',
            'Job execution duration',
            ['job_name']
        )
        self.listings_scraped = Counter(
            'realestate_listings_scraped_total',
            'Total listings scraped',
            ['portal']
        )
        self.listings_processed = Counter(
            'realestate_listings_processed_total',
            'Total listings processed by ETL',
            ['stage']
        )
        self.valuations_computed = Counter(
            'realestate_valuations_computed_total',
            'Total valuations computed'
        )
        self.scores_computed = Counter(
            'realestate_scores_computed_total',
            'Total scores computed'
        )
        self.notifications_sent = Counter(
            'realestate_notifications_sent_total',
            'Total notifications sent',
            ['channel']
        )
        self.model_accuracy = Gauge(
            'realestate_model_accuracy',
            'Current model accuracy',
            ['model_name']
        )
        self.model_drift = Gauge(
            'realestate_model_drift_score',
            'Data drift score',
            ['model_name']
        )
        self.db_connections = Gauge(
            'realestate_db_connections_active',
            'Active database connections'
        )
        self.pipeline_latency = Histogram(
            'realestate_pipeline_latency_seconds',
            'End-to-end pipeline latency'
        )

        # Business metrics
        self.opportunities_found = Counter(
            'realestate_opportunities_found_total',
            'Total investment opportunities found',
            ['classification']
        )
        self.avg_discount = Gauge(
            'realestate_avg_discount_percent',
            'Average discount percentage across all listings'
        )
        self.market_price_trend = Gauge(
            'realestate_market_price_trend',
            'Market price trend (positive = increasing)',
            ['freguesia']
        )
        self.active_listings_count = Gauge(
            'realestate_active_listings_count',
            'Number of active listings in database'
        )
        self.high_score_count = Gauge(
            'realestate_high_score_listings',
            'Number of listings with score >= 8'
        )

        # Performance metrics
        self.api_request_duration = Histogram(
            'realestate_api_request_duration_seconds',
            'External API request duration',
            ['api_name']
        )
        self.cache_hit_rate = Gauge(
            'realestate_cache_hit_rate',
            'Cache hit rate percentage',
            ['cache_type']
        )
        self.memory_usage = Gauge(
            'realestate_memory_usage_bytes',
            'Process memory usage in bytes'
        )

        # System info
        self.system_info = Info(
            'realestate_system_info',
            'System information'
        )

        # Alerting thresholds
        self.alerts_triggered = Counter(
            'realestate_alerts_triggered_total',
            'Alerts triggered',
            ['alert_type', 'severity']
        )

        # Data quality metrics
        self.data_quality_score = Gauge(
            'realestate_data_quality_score',
            'Data quality score by dimension and field',
            ['dimension', 'field', 'portal']
        )
        self.data_quality_completeness = Gauge(
            'realestate_data_quality_completeness',
            'Field completeness percentage',
            ['field', 'portal']
        )
        self.data_quality_accuracy = Gauge(
            'realestate_data_quality_accuracy',
            'Field accuracy percentage',
            ['field', 'portal']
        )

        # In-memory metrics
        self._latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._errors: Dict[str, int] = defaultdict(int)
        self._custom: Dict[str, Any] = {}
        self._alerts_history: List[Dict[str, Any]] = []
        self._initialized = True
    
    def start_server(self):
        """Start Prometheus metrics HTTP server."""
        if not self._started:
            try:
                start_http_server(self.port)
                self._started = True
                logger.info(f"Prometheus metrics server started on port {self.port}")
            except Exception as e:
                logger.warning(f"Could not start Prometheus server: {e}")
    
    def record_job(self, job_name: str, status: str, duration: Optional[float] = None):
        """Record job execution metric."""
        self.jobs_total.labels(job_name=job_name, status=status).inc()
        if duration:
            self.job_duration.labels(job_name=job_name).observe(duration)
    
    def record_listings_scraped(self, portal: str, count: int = 1):
        """Record listings scraped."""
        self.listings_scraped.labels(portal=portal).inc(count)
    
    def record_listings_processed(self, stage: str, count: int = 1):
        """Record listings processed."""
        self.listings_processed.labels(stage=stage).inc(count)
    
    def record_valuation(self):
        """Record valuation computed."""
        self.valuations_computed.inc()
    
    def record_score(self):
        """Record score computed."""
        self.scores_computed.inc()
    
    def record_notification(self, channel: str = "telegram"):
        """Record notification sent."""
        self.notifications_sent.labels(channel=channel).inc()
    
    def record_latency(self, operation: str, seconds: float):
        """Record operation latency."""
        self._latencies[operation].append(seconds)
        if operation.startswith("job_"):
            self.job_duration.labels(job_name=operation).observe(seconds)
    
    def record_error(self, operation: str):
        """Record operation error."""
        self._errors[operation] += 1

    def record_event(self, event_name: str, value: float = 1.0):
        """Record a generic business event (freeform counter/gauge).

        Used by DataQuality checks and ad-hoc pipeline signals.
        """
        self._custom.setdefault(event_name, []).append(float(value))
    
    def set_model_accuracy(self, model_name: str, accuracy: float):
        """Set model accuracy gauge."""
        self.model_accuracy.labels(model_name=model_name).set(accuracy)
    
    def set_model_drift(self, model_name: str, drift: float):
        """Set model drift gauge."""
        self.model_drift.labels(model_name=model_name).set(drift)
    
    def get_latency_stats(self, operation: str) -> Dict[str, float]:
        """Get latency statistics for an operation."""
        import statistics
        values = list(self._latencies.get(operation, []))
        if not values:
            return {}
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }
    
    def get_error_count(self, operation: str) -> int:
        """Get error count for an operation."""
        return self._errors.get(operation, 0)
    
    def reset(self):
        """Reset in-memory metrics."""
        self._latencies.clear()
        self._errors.clear()
        self._custom.clear()
    
    def record_opportunity(self, classification: str):
        """Record investment opportunity found."""
        self.opportunities_found.labels(classification=classification).inc()
    
    def update_avg_discount(self, discount_percent: float):
        """Update average discount metric."""
        self.avg_discount.set(discount_percent)
    
    def update_market_trend(self, freguesia: str, trend: float):
        """Update market price trend for a region."""
        self.market_price_trend.labels(freguesia=freguesia).set(trend)
    
    def update_active_listings(self, count: int):
        """Update active listings count."""
        self.active_listings_count.set(count)
    
    def update_high_score_count(self, count: int):
        """Update high score listings count."""
        self.high_score_count.set(count)
    
    def record_api_request(self, api_name: str, duration: float):
        """Record external API request duration."""
        self.api_request_duration.labels(api_name=api_name).observe(duration)
    
    def update_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Update cache hit rate."""
        self.cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)
    
    def update_memory_usage(self):
        """Update memory usage metric."""
        import psutil
        process = psutil.Process()
        self.memory_usage.set(process.memory_info().rss)
    
    def set_system_info(self, version: str, environment: str):
        """Set system information."""
        self.system_info.info({
            'version': version,
            'environment': environment,
            'python_version': '3.8+',
        })
    
    def trigger_alert(self, alert_type: str, severity: str, message: str):
        """Trigger an alert."""
        self.alerts_triggered.labels(alert_type=alert_type, severity=severity).inc()
        self._alerts_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': alert_type,
            'severity': severity,
            'message': message,
        })
        # Keep only last 100 alerts
        if len(self._alerts_history) > 100:
            self._alerts_history = self._alerts_history[-100:]
    
    def get_alerts_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts history."""
        return self._alerts_history[-limit:]
    
    def get_business_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of business metrics."""
        return {
            'opportunities_by_classification': dict(self.opportunities_found._metrics[0]._samples),
            'avg_discount': self.avg_discount._value.get(),
            'active_listings': self.active_listings_count._value.get(),
            'high_score_listings': self.high_score_count._value.get(),
        }
