"""Data quality metrics tracking for ETL pipeline.

Tracks completeness, accuracy, consistency, timeliness, and uniqueness
of data across the ETL pipeline with Prometheus integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from loguru import logger

from realestate_engine.monitoring.metrics import MetricsCollector


class DataQualityDimension(Enum):
    """Dimensions of data quality to track."""
    COMPLETENESS = "completeness"  # % of non-null fields
    ACCURACY = "accuracy"  # % of valid values
    CONSISTENCY = "consistency"  # % of consistent cross-field values
    TIMELINESS = "timeliness"  # age of data
    UNIQUENESS = "uniqueness"  # % of unique records


@dataclass
class DataQualityMetric:
    """Single data quality metric measurement."""
    dimension: DataQualityDimension
    field: str
    total_count: int
    valid_count: int
    invalid_count: int
    score: float  # 0-100
    timestamp: datetime
    portal: str

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DataQualityTracker:
    """Track data quality metrics across ETL pipeline."""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.metrics: List[DataQualityMetric] = []

    def track_completeness(self, listings: List[Dict], portal: str):
        """Track field completeness (% of non-null required fields)."""
        required_fields = [
            "source_portal", "source_id", "preco_pedido", "area_util_m2",
            "quartos", "freguesia", "concelho", "distrito"
        ]
        optional_fields = [
            "titulo", "descricao", "casas_banho", "tipologia", "estado",
            "ano_construcao", "certificado_energetico", "morada"
        ]

        all_fields = required_fields + optional_fields

        for field in all_fields:
            total = len(listings)
            valid = sum(1 for listing in listings if listing.get(field) is not None and listing.get(field) != "")
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0

            metric = DataQualityMetric(
                dimension=DataQualityDimension.COMPLETENESS,
                field=field,
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)

            # Update Prometheus
            if hasattr(self.metrics_collector, 'data_quality_completeness'):
                self.metrics_collector.data_quality_completeness.labels(field=field, portal=portal).set(score)

            # Alert if low completeness for required fields
            if field in required_fields and score < 80:
                logger.warning(
                    f"Low completeness for required field {field} in {portal}: {score:.1f}% "
                    f"({valid}/{total})"
                )

    def track_accuracy(self, listings: List[Dict], portal: str):
        """Track field accuracy (valid values within expected ranges)."""
        accuracy_checks = {
            "preco_pedido": lambda x: x is not None and x > 0,
            "area_util_m2": lambda x: x is not None and x > 0,
            "area_bruta_m2": lambda x: x is not None and x > 0,
            "quartos": lambda x: x is not None and 0 <= x <= 20,
            "casas_banho": lambda x: x is not None and 0 <= x <= 10,
            "lat": lambda x: x is not None and -90 <= x <= 90,
            "lon": lambda x: x is not None and -180 <= x <= 180,
            "ano_construcao": lambda x: x is not None and 1900 <= x <= 2030,
        }

        for field, check in accuracy_checks.items():
            total = len(listings)
            valid = sum(1 for listing in listings if check(listing.get(field)))
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0

            metric = DataQualityMetric(
                dimension=DataQualityDimension.ACCURACY,
                field=field,
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)

            # Update Prometheus
            if hasattr(self.metrics_collector, 'data_quality_accuracy'):
                self.metrics_collector.data_quality_accuracy.labels(field=field, portal=portal).set(score)

            if score < 90:
                logger.warning(
                    f"Low accuracy for {field} in {portal}: {score:.1f}% "
                    f"({valid}/{total})"
                )

    def track_consistency(self, listings: List[Dict], portal: str):
        """Track cross-field consistency."""
        consistency_checks = [
            # Price per m² should be reasonable (100-10000 EUR/m²)
            lambda x: x.get("preco_por_m2") is None or 100 <= x.get("preco_por_m2") <= 10000,
            # Area should match rooms (T1: 30-80m², T3: 60-150m², etc.)
            # Simplified check: area should be at least 20m² per room
            lambda x: x.get("area_util_m2") is None or x.get("quartos") is None or x.get("area_util_m2") >= x.get("quartos") * 20,
            # Longitude should be within Portugal range if latitude is provided
            lambda x: x.get("lat") is None or x.get("lon") is None or (-9.5 <= x.get("lon") <= -6.2 if 36 <= x.get("lat") <= 42 else True),
        ]

        for i, check in enumerate(consistency_checks):
            total = len(listings)
            valid = sum(1 for listing in listings if check(listing))
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0

            metric = DataQualityMetric(
                dimension=DataQualityDimension.CONSISTENCY,
                field=f"cross_field_check_{i}",
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)

            if score < 85:
                logger.warning(
                    f"Low consistency for cross-field check {i} in {portal}: {score:.1f}% "
                    f"({valid}/{total})"
                )

    def track_uniqueness(self, listings: List[Dict], portal: str):
        """Track record uniqueness (duplicate source_id detection)."""
        source_ids = [listing.get("source_id") for listing in listings]
        unique_ids = set(source_ids)
        total = len(listings)
        unique_count = len(unique_ids)
        duplicate_count = total - unique_count
        score = (unique_count / total * 100) if total > 0 else 0

        metric = DataQualityMetric(
            dimension=DataQualityDimension.UNIQUENESS,
            field="source_id",
            total_count=total,
            valid_count=unique_count,
            invalid_count=duplicate_count,
            score=score,
            timestamp=datetime.now(),
            portal=portal
        )
        self.metrics.append(metric)

        if duplicate_count > 0:
            logger.warning(
                f"Duplicate source_ids detected in {portal}: {duplicate_count} duplicates "
                f"({unique_count}/{total} unique)"
            )

    def get_quality_report(self, portal: Optional[str] = None) -> Dict:
        """Generate quality report by dimension, field, and portal."""
        metrics = self.metrics if portal is None else [m for m in self.metrics if m.portal == portal]

        if not metrics:
            return {
                "overall_score": 0,
                "by_dimension": {},
                "by_field": {},
                "by_portal": {},
                "total_metrics": 0
            }

        report = {
            "overall_score": sum(m.score for m in metrics) / len(metrics),
            "by_dimension": {},
            "by_field": {},
            "by_portal": {},
            "total_metrics": len(metrics)
        }

        # Group by dimension
        for dim in DataQualityDimension:
            dim_metrics = [m for m in metrics if m.dimension == dim]
            if dim_metrics:
                dim_score = sum(m.score for m in dim_metrics) / len(dim_metrics)
                report["by_dimension"][dim.value] = {
                    "score": dim_score,
                    "metric_count": len(dim_metrics),
                    "metrics": [
                        {
                            "field": m.field,
                            "score": m.score,
                            "total": m.total_count,
                            "valid": m.valid_count,
                            "invalid": m.invalid_count
                        }
                        for m in dim_metrics
                    ]
                }

        # Group by field
        for metric in metrics:
            if metric.field not in report["by_field"]:
                report["by_field"][metric.field] = []
            report["by_field"][metric.field].append({
                "dimension": metric.dimension.value,
                "score": metric.score,
                "portal": metric.portal,
                "total": metric.total_count,
                "valid": metric.valid_count,
                "invalid": metric.invalid_count
            })

        # Group by portal
        for metric in metrics:
            if metric.portal not in report["by_portal"]:
                report["by_portal"][metric.portal] = []
            report["by_portal"][metric.portal].append({
                "dimension": metric.dimension.value,
                "field": metric.field,
                "score": metric.score
            })

        return report

    def alert_if_degraded(self, threshold: float = 80.0):
        """Alert if quality score below threshold."""
        report = self.get_quality_report()

        if report["overall_score"] < threshold:
            logger.error(
                f"Data quality degraded: {report['overall_score']:.1f}% "
                f"(threshold: {threshold}%)"
            )

        # Check individual dimensions
        for dim_name, dim_data in report["by_dimension"].items():
            if dim_data["score"] < threshold:
                logger.error(
                    f"Data quality degraded for {dim_name}: {dim_data['score']:.1f}% "
                    f"(threshold: {threshold}%)"
                )

    def get_overall_score(self) -> float:
        """Calculate overall quality score (average of all metrics)."""
        if not self.metrics:
            return 0.0
        return sum(m.score for m in self.metrics) / len(self.metrics)

    def get_metrics_by_dimension(self, dimension: DataQualityDimension) -> List[DataQualityMetric]:
        """Get metrics filtered by dimension."""
        return [m for m in self.metrics if m.dimension == dimension]

    def get_low_quality_fields(self, threshold: float = 80.0) -> List[str]:
        """Identify fields with score below threshold."""
        low_quality = set()
        for m in self.metrics:
            if m.score < threshold:
                low_quality.add(m.field)
        return sorted(low_quality)

    def clear_metrics(self):
        """Clear all metrics (useful for testing or periodic reset)."""
        self.metrics.clear()
        logger.info("Data quality metrics cleared")
