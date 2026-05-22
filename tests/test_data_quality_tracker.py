"""Tests for DataQualityTracker from Phase 3 ETL Data Quality Audit."""
import pytest
from realestate_engine.etl.data_quality_tracker import (
    DataQualityTracker,
    DataQualityDimension,
    DataQualityMetric
)


def _make_listing(**kwargs):
    """Create a minimal valid listing for testing."""
    defaults = {
        "source_portal": "idealista",
        "source_id": "test-001",
        "source_url": "https://example.com/1",
        "scrape_timestamp": "2024-01-01",
        "titulo": "Test",
        "descricao": "Test desc",
        "preco_pedido": 250000,
        "area_util_m2": 85,
        "quartos": 2,
        "freguesia": "Cedofeita",
        "concelho": "Porto",
        "distrito": "Porto",
        "casas_banho": 1,
        "tipologia": "T2",
        "estado": "usado",
        "ano_construcao": 2000,
        "certificado_energetico": "B",
        "morada": "Rua Teste",
    }
    defaults.update(kwargs)
    return defaults


class TestDataQualityTracker:
    """Test suite for DataQualityTracker class."""

    def test_initialization(self):
        """Test DataQualityTracker initialization."""
        tracker = DataQualityTracker()
        assert tracker is not None
        assert tracker.metrics is not None
        assert len(tracker.metrics) == 0

    def test_track_completeness(self):
        """Test completeness tracking."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing(), _make_listing(area_util_m2=None)]
        tracker.track_completeness(listings, portal="idealista")
        assert len(tracker.metrics) > 0
        # area_util_m2 should have 2/3 = 66.7%
        area_metric = [m for m in tracker.metrics if m.field == "area_util_m2"][0]
        assert area_metric.dimension == DataQualityDimension.COMPLETENESS
        assert area_metric.score == pytest.approx(66.67, rel=0.01)

    def test_track_accuracy(self):
        """Test accuracy tracking."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing(preco_pedido=-1), _make_listing(area_util_m2=0)]
        tracker.track_accuracy(listings, portal="idealista")
        assert len(tracker.metrics) > 0
        preco_metric = [m for m in tracker.metrics if m.field == "preco_pedido"][0]
        assert preco_metric.dimension == DataQualityDimension.ACCURACY
        assert preco_metric.score == pytest.approx(66.67, rel=0.01)

    def test_track_consistency(self):
        """Test consistency tracking."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing(), _make_listing(preco_por_m2=50000)]
        tracker.track_consistency(listings, portal="idealista")
        assert len(tracker.metrics) > 0
        assert all(m.dimension == DataQualityDimension.CONSISTENCY for m in tracker.metrics)

    def test_track_uniqueness(self):
        """Test uniqueness tracking."""
        tracker = DataQualityTracker()
        listings = [_make_listing(source_id="a"), _make_listing(source_id="a"), _make_listing(source_id="b")]
        tracker.track_uniqueness(listings, portal="idealista")
        assert len(tracker.metrics) == 1
        metric = tracker.metrics[0]
        assert metric.dimension == DataQualityDimension.UNIQUENESS
        assert metric.score == pytest.approx(66.67, rel=0.01)  # 2 unique / 3 total

    def test_calculate_overall_score(self):
        """Test overall data quality score calculation."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing(), _make_listing()]
        tracker.track_completeness(listings, portal="idealista")
        tracker.track_accuracy(listings, portal="idealista")
        overall_score = tracker.get_overall_score()
        assert overall_score > 0

    def test_get_metrics_by_dimension(self):
        """Test filtering metrics by dimension."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing()]
        tracker.track_completeness(listings, portal="idealista")
        tracker.track_accuracy(listings, portal="idealista")
        completeness_metrics = tracker.get_metrics_by_dimension(DataQualityDimension.COMPLETENESS)
        assert len(completeness_metrics) > 0
        assert all(m.dimension == DataQualityDimension.COMPLETENESS for m in completeness_metrics)

    def test_get_low_quality_fields(self):
        """Test identification of low-quality fields."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing(), _make_listing(area_util_m2=None)]
        tracker.track_completeness(listings, portal="idealista")
        low_quality = tracker.get_low_quality_fields(threshold=80.0)
        assert "area_util_m2" in low_quality

    def test_get_quality_report(self):
        """Test generation of quality report."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing()]
        tracker.track_completeness(listings, portal="idealista")
        tracker.track_accuracy(listings, portal="idealista")
        report = tracker.get_quality_report()
        assert "overall_score" in report
        assert "by_dimension" in report
        assert "by_field" in report
        assert "by_portal" in report

    def test_clear_metrics(self):
        """Test clearing all metrics."""
        tracker = DataQualityTracker()
        listings = [_make_listing(), _make_listing()]
        tracker.track_completeness(listings, portal="idealista")
        assert len(tracker.metrics) > 0
        tracker.clear_metrics()
        assert len(tracker.metrics) == 0

    def test_metric_timestamp(self):
        """Test metrics have timestamps."""
        tracker = DataQualityTracker()
        listings = [_make_listing()]
        tracker.track_completeness(listings, portal="idealista")
        metric = tracker.metrics[0]
        assert metric.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
