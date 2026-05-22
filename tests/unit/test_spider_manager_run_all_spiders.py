"""Regression tests for SpiderManager scraping orchestration."""

import pytest

from realestate_engine.scraping.spider_manager import SpiderManager


@pytest.mark.asyncio
async def test_run_all_spiders_returns_flattened_results(monkeypatch):
    """run_all_spiders should remain backward-compatible for scheduler jobs."""
    spider_manager = SpiderManager()

    async def fake_run_spider(portal, max_pages=20, headless=True):
        return [
            {"source_portal": portal, "source_id": f"{portal}-1"},
            {"source_portal": portal, "source_id": f"{portal}-2"},
        ]

    monkeypatch.setattr(spider_manager, "run_spider", fake_run_spider)

    results = await spider_manager.run_all_spiders(["imovirtual", "casa_sapo"])

    assert isinstance(results, list)
    assert len(results) == 4
    assert {item["source_portal"] for item in results} == {"imovirtual", "casa_sapo"}
    assert results[0]["source_id"] == "imovirtual-1"
    assert results[-1]["source_id"] == "casa_sapo-2"
