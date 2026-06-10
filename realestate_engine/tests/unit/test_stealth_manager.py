"""Unit tests for StealthManager (Advanced 2026)."""
import pytest
from realestate_engine.scraping.stealth_manager import StealthManager

class TestStealthManager:
    """Test stealth manager functions."""

    def test_init(self):
        sm = StealthManager()
        assert sm.locale == "pt-PT"
        assert sm.timezone == "Europe/Lisbon"

    def test_get_browser_args(self):
        sm = StealthManager()
        args = sm.get_browser_args()
        assert any("--user-agent=" in arg for arg in args)
        assert any("--lang=pt-PT" in arg for arg in args)
        assert "--no-sandbox" in args

    @pytest.mark.asyncio
    async def test_apply_stealth_smoke(self):
        # Mock tab object
        class MockTab:
            async def evaluate(self, script):
                return True
        
        sm = StealthManager()
        await sm.apply_stealth(MockTab())
        # Should not raise exception
