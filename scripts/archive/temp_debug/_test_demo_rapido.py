"""Test Demo Rápido (casa_sapo spider) with ProactorEventLoop fix.

This test simulates what happens when clicking "Demo Rápido (~30s)" in the dashboard.
It runs the casa_sapo spider with max_pages=1 using the _run_async wrapper.

Run: ``venv312\\Scripts\\python.exe scripts\\debug\\_test_demo_rapido.py``
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.dashboard.views.scraping_results import _run_async
from realestate_engine.scraping.spider_manager import SpiderManager


async def test_demo_rapido():
    """Test Demo Rápido: casa_sapo spider with max_pages=1."""
    spider_mgr = SpiderManager()
    portal = "casa_sapo"
    max_pages = 1  # Demo Rápido uses 1 page only
    
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
    print("Testing Demo Rápido (casa_sapo, max_pages=1)...")
    print()
    
    try:
        count = _run_async(test_demo_rapido())
        print()
        print(f"=== Demo Rápido Test Result ===")
        print(f"✅ SUCCESS: {count} listings scraped")
        print(f"   The ProactorEventLoop fix works on Windows!")
        return 0
    except NotImplementedError as e:
        print()
        print(f"=== Demo Rápido Test Result ===")
        print(f"❌ FAILED: ProactorEventLoop not working")
        print(f"   Error: {e}")
        return 1
    except Exception as e:
        print()
        print(f"=== Demo Rápido Test Result ===")
        print(f"❌ FAILED: Unexpected error")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
