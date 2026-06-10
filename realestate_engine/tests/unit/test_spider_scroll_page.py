"""Tests for BaseSpiderNodriver.scroll_page fix.

Validates that scroll_page method exists and handles tab evaluation errors gracefully.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver


class DummySpider(BaseSpiderNodriver):
    name = "dummy"
    base_url = "https://example.com"

    async def parse_page(self, page_num):
        return []

    async def get_next_page(self):
        return False


@pytest.mark.asyncio
async def test_scroll_page_exists_and_evaluates():
    """scroll_page must call tab.evaluate the requested number of times."""
    spider = DummySpider()
    spider.tab = MagicMock()
    spider.tab.evaluate = AsyncMock(return_value=None)

    with patch("asyncio.sleep", new=AsyncMock()):
        await spider.scroll_page(scroll_count=3)

    assert spider.tab.evaluate.call_count == 3


@pytest.mark.asyncio
async def test_scroll_page_graceful_on_error():
    """scroll_page must not crash if tab.evaluate raises."""
    spider = DummySpider()
    spider.tab = MagicMock()
    spider.tab.evaluate = AsyncMock(side_effect=Exception("tab closed"))

    with patch("asyncio.sleep", new=AsyncMock()):
        await spider.scroll_page(scroll_count=5)

    # Should break after first failure, not crash
    assert spider.tab.evaluate.call_count == 1
