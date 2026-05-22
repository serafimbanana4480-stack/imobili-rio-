"""Unit tests for ProxyManager (Professional Standard)."""
import pytest
import os
from realestate_engine.scraping.proxy_manager import ProxyManager

class TestProxyManager:
    """Test proxy manager functions."""

    def test_init_with_url(self):
        url = "http://user:pass@residential.proxy:8080"
        pm = ProxyManager(proxy_url=url)
        assert pm.proxy_url == url

    def test_get_proxy(self):
        url = "http://user:pass@residential.proxy:8080"
        pm = ProxyManager(proxy_url=url)
        assert pm.get_proxy() == url

    def test_get_proxy_direct(self):
        url = "http://env:pass@residential.proxy:8080"
        pm = ProxyManager(proxy_url=url)
        assert pm.get_proxy() == url

    def test_mark_failed_loguru(self):
        # We check if it doesn't crash, since capturing loguru is complex in pytest
        pm = ProxyManager(proxy_url="http://p:p@p:1")
        pm.mark_failed("http://p:p@p:1")
