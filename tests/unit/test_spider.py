"""Test individual spiders to identify which work."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from realestate_engine.scraping.spider_manager import SpiderManager

async def test_spiders():
    """Test each spider individually."""
    spider_mgr = SpiderManager()
    
    portals = ["idealista", "imovirtual", "casa_sapo", "era"]
    
    for portal in portals:
        print(f"\n{'='*50}")
        print(f"Testing {portal}...")
        print('='*50)
        try:
            results = await spider_mgr.run_spider(portal, max_pages=1)
            print(f"✓ {portal}: {len(results)} listings found")
            if results:
                print(f"Sample: {results[0]}")
        except Exception as e:
            print(f"✗ {portal}: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(test_spiders())
