"""Test era spider (nodriver + Chrome) with ProactorEventLoop fix.

Run: ``venv312\\Scripts\\python.exe scripts\\debug\\_test_era.py``
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.dashboard.views.scraping_results import _run_async
from realestate_engine.scraping.spider_manager import SpiderManager


async def test_era():
    """Test era spider with max_pages=1 (uses nodriver + Chrome)."""
    spider_mgr = SpiderManager()
    portal = "era"
    max_pages = 1
    
    print(f"Starting spider: {portal} (Max pages: {max_pages})")
    
    try:
        results = await spider_mgr.run_spider(
            portal,
            max_pages=max_pages,
            headless=True,
        )
        count = len(results) if results else 0
        print(f"✅ Spider completed successfully: {count} listings scraped")
        return count
    except NotImplementedError as e:
        print(f"❌ NotImplementedError (ProactorEventLoop not working): {e}")
        raise
    except Exception as e:
        print(f"❌ Spider failed: {e}")
        raise


def main() -> int:
    print(f"Platform: {sys.platform}")
    print("Testing era spider (nodriver + Chrome, max_pages=1)...")
    print()
    
    try:
        count = _run_async(test_era())
        print()
        print(f"✅ SUCCESS: {count} listings scraped")
        print(f"   ProactorEventLoop fix confirmed working!")
        return 0
    except NotImplementedError as e:
        print(f"❌ FAILED: {e}")
        return 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
