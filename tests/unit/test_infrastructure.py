"""Tests for infrastructure components: EventBus, Worker, PrometheusExporter."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from realestate_engine.infrastructure.event_bus import EventBus, DomainEvent
from realestate_engine.infrastructure.worker import Worker, ETLWorker
from realestate_engine.infrastructure.metrics_exporter import PrometheusExporter, get_exporter


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    handler = AsyncMock()
    bus.subscribe("ListingScraped", handler)

    event = EventBus.listing_scraped({"source_id": "abc"})
    await bus.publish(event)

    handler.assert_awaited_once()
    assert handler.call_args[0][0].event_type == "ListingScraped"


@pytest.mark.asyncio
async def test_event_bus_multiple_handlers():
    bus = EventBus()
    h1 = AsyncMock()
    h2 = AsyncMock()
    bus.subscribe("PriceChanged", h1)
    bus.subscribe("PriceChanged", h2)

    event = EventBus.price_changed("id1", 100000.0, 95000.0)
    await bus.publish(event)

    h1.assert_awaited_once()
    h2.assert_awaited_once()


@pytest.mark.asyncio
async def test_event_bus_handler_error_isolated():
    bus = EventBus()
    bad = AsyncMock(side_effect=Exception("boom"))
    good = AsyncMock()
    bus.subscribe("ScoreComputed", bad)
    bus.subscribe("ScoreComputed", good)

    event = EventBus.score_computed("id1", {"score_total": 8.5})
    await bus.publish(event)

    bad.assert_awaited_once()
    good.assert_awaited_once()


def test_prometheus_exporter_counters_and_gauges():
    exp = PrometheusExporter()
    exp.inc("scrape_listings_total", 10, {"portal": "idealista"})
    exp.inc("scrape_listings_total", 5, {"portal": "imovirtual"})
    exp.set_gauge("proxy_health_score", 0.85)

    text = exp.render()
    assert "scrape_listings_total{portal=\"idealista\"} 10" in text
    assert "scrape_listings_total{portal=\"imovirtual\"} 5" in text
    assert "proxy_health_score 0.85" in text


def test_prometheus_exporter_histogram():
    exp = PrometheusExporter()
    exp.observe("etl_duration_seconds", 1.5)
    exp.observe("etl_duration_seconds", 2.5)

    text = exp.render()
    assert "etl_duration_seconds_sum 4.0000" in text
    assert "etl_duration_seconds_count 2" in text


def test_prometheus_singleton():
    e1 = get_exporter()
    e2 = get_exporter()
    assert e1 is e2


@pytest.mark.asyncio
async def test_worker_lifecycle():
    worker = Worker(name="TestWorker", heartbeat_interval=1)
    task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.5)
    worker._request_shutdown()
    await asyncio.wait_for(task, timeout=3)
    assert worker._stats["processed"] == 0


@pytest.mark.asyncio
async def test_worker_records_success_and_error():
    worker = Worker(name="TestWorker")
    worker.record_success()
    worker.record_success()
    worker.record_error()
    assert worker._stats["processed"] == 2
    assert worker._stats["errors"] == 1
