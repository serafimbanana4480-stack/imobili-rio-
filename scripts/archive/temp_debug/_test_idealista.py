"""Test idealista spider (nodriver + Chrome) with ProactorEventLoop fix.

This test verifies that nodriver's Chrome subprocess works on Windows with
the ProactorEventLoop policy fix.

Run: ``venv312\\Scripts\\python.exe scripts\\debug\\_test_idealista.py``
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.dashboard.views.scraping_results import _run_async
from realestate_engine.scraping.spider_manager import SpiderManager


async def test_idealista():
    """Test idealista spider with max_pages=1 (uses nodriver + Chrome)."""
    spider_mgr = SpiderManager()
    portal = "idealista"
    max_pages = 1  # Quick test
    
    print(f"Starting spider: {portal} (Max pages: {max_pages})")
    print(f"  This uses nodriver + Chrome subprocess - the critical test case")
    
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
    print("Testing idealista spider (nodriver + Chrome, max_pages=1)...")
    print()
    
    try:
        count = _run_async(test_idealista())
        print()
        print(f"=== Pipeline Completo Test Result ===")
        print(f"✅ SUCCESS: {count} listings scraped")
        print(f"   The ProactorEventLoop fix works with nodriver + Chrome on Windows!")
        return 0
    except NotImplementedError as e:
        print()
        print(f"=== Pipeline Completo Test Result ===")
        print(f"❌ FAILED: ProactorEventLoop not working for nodriver")
        print(f"   Error: {e}")
        return 1
    except Exception as e:
        print()
        print(f"=== Pipeline Completo Test Result ===")
        print(f"❌ FAILED: Unexpected error")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
