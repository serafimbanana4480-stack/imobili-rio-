"""Tests for Redis health check graceful degradation."""
import pytest
from unittest.mock import patch, MagicMock

from realestate_engine.monitoring.health_checks import HealthCheck


@pytest.fixture
def hc():
    return HealthCheck()


def test_redis_not_configured_returns_degraded(hc):
    """When Redis URL is default localhost and no server is running, status should be degraded, not unhealthy."""
    mock_cfg = MagicMock()
    mock_cfg.redis_url = "redis://localhost:6379/0"
    with patch("realestate_engine.monitoring.health_checks.config", mock_cfg):
        result = hc.check_redis()
    assert result["status"] == "degraded"
    assert "optional" in result.get("note", "").lower() or "not configured" in result.get("note", "").lower()


def test_redis_custom_url_but_unavailable(hc):
    """If a custom Redis URL is set but server is down, should report degraded with error."""
    mock_cfg = MagicMock()
    mock_cfg.redis_url = "redis://fake-host:9999/1"
    with patch("realestate_engine.monitoring.health_checks.config", mock_cfg):
        result = hc.check_redis()
    assert result["status"] == "degraded"
    assert "error" in result or "optional" in result.get("note", "").lower()
