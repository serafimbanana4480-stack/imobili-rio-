"""Tests for DataQualityEngine drift detection, anomaly detection, and schema validation."""
import pytest
from realestate_engine.monitoring.data_quality import DataQualityEngine


def test_schema_validation_passes():
    dq = DataQualityEngine()
    record = {
        "source_portal": "idealista",
        "source_id": "abc123",
        "preco_pedido": 250000.0,
        "area_util_m2": 85,
        "quartos": 2,
        "lat": 41.15,
        "lon": -8.61,
    }
    errors = dq.validate_schema(record)
    assert errors == []


def test_schema_validation_missing_field():
    dq = DataQualityEngine()
    record = {
        "source_portal": "idealista",
        "source_id": "abc123",
        "area_util_m2": 85,
        "quartos": 2,
    }
    errors = dq.validate_schema(record)
    assert any("preco_pedido" in e for e in errors)


def test_schema_validation_type_mismatch():
    dq = DataQualityEngine()
    record = {
        "source_portal": "idealista",
        "source_id": "abc123",
        "preco_pedido": "muito caro",
        "area_util_m2": 85,
        "quartos": 2,
        "lat": 41.15,
        "lon": -8.61,
    }
    errors = dq.validate_schema(record)
    assert any("preco_pedido" in e and "Type mismatch" in e for e in errors)


def test_batch_stats():
    dq = DataQualityEngine()
    records = [
        {"preco_pedido": 100000.0, "area_util_m2": 50, "preco_por_m2": 2000.0},
        {"preco_pedido": 200000.0, "area_util_m2": 100, "preco_por_m2": 2000.0},
        {"preco_pedido": 300000.0, "area_util_m2": 150, "preco_por_m2": 2000.0},
    ]
    stats = dq.calculate_batch_stats(records)
    assert "preco_pedido" in stats
    assert stats["preco_pedido"]["mean"] == 200000.0


def test_drift_detection():
    dq = DataQualityEngine()
    baseline = [{"preco_pedido": 200000.0, "area_util_m2": 100, "preco_por_m2": 2000.0} for _ in range(20)]
    dq.detect_drift(dq.calculate_batch_stats(baseline))  # establish baseline

    # Now inject a big shift
    shifted = [{"preco_pedido": 500000.0, "area_util_m2": 100, "preco_por_m2": 5000.0} for _ in range(20)]
    alerts = dq.detect_drift(dq.calculate_batch_stats(shifted))
    assert len(alerts) > 0
    assert any("preco_pedido" in a for a in alerts)


def test_price_anomalies():
    dq = DataQualityEngine()
    records = [{"preco_pedido": float(p), "source_id": f"id{i}"} for i, p in enumerate(range(100000, 200000, 10000))]
    # Add extreme outlier
    records.append({"preco_pedido": 9999999.0, "source_id": "outlier"})
    anomalies = dq.detect_price_anomalies(records)
    assert len(anomalies) == 1
    assert anomalies[0]["source_id"] == "outlier"


def test_freshness():
    dq = DataQualityEngine()
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    fresh = [{"scrape_timestamp": now.isoformat()} for _ in range(5)]
    stale = [{"scrape_timestamp": (now - timedelta(days=3)).isoformat()} for _ in range(3)]
    alerts = dq.check_freshness(fresh + stale, max_age_hours=48)
    assert len(alerts) == 1
    assert "3" in alerts[0] or "8" in alerts[0]


def test_full_check_healthy():
    dq = DataQualityEngine()
    from datetime import datetime, timezone
    records = [
        {
            "source_portal": "idealista",
            "source_id": f"id{i}",
            "preco_pedido": 200000.0 + i * 1000,
            "area_util_m2": 80 + i,
            "quartos": 2,
            "lat": 41.15,
            "lon": -8.61,
            "scrape_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for i in range(10)
    ]
    report = dq.run_full_check(records)
    assert report["healthy"] is True
    assert report["record_count"] == 10
