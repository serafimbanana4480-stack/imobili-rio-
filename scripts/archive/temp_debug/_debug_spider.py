"""Debug spider crash."""
import asyncio
import sys
sys.path.insert(0, '.')

from realestate_engine.scraping.spiders.imovirtual_nextdata_spider import ImovirtualNextDataSpider

async def debug():
    spider = ImovirtualNextDataSpider()
    spider.SEARCH_URLS = [spider.SEARCH_URLS[0]]  # Only Porto
    spider.max_pages = 5
    
    print("Starting spider...")
    try:
        results = await spider.run(max_pages=5)
        print(f"SUCCESS: {len(results)} results")
    except Exception as e:
        import traceback
        print(f"ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()

asyncio.run(debug())
