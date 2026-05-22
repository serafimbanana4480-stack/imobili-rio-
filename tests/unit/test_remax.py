
import asyncio
import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider

async def test_remax():
    spider = REMAXDirectSpider()
    print("Starting REMAX spider test...")
    results = await spider.run(max_pages=1)
    print(f"Scraped {len(results)} listings")
    if results:
        print(f"Sample: {results[0]['source_url']}")
    else:
        print("No results found. Stats:")
        print(spider.stats)

if __name__ == "__main__":
    asyncio.run(test_remax())
