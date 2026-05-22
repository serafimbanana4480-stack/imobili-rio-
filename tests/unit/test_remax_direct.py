"""Test REMAX Direct spider standalone."""
import asyncio
import sys
sys.path.insert(0, '.')

from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider

async def main():
    spider = REMAXDirectSpider()
    print("Testing REMAX Direct spider with max_pages=1 (15 listings)...")
    results = await spider.run(max_pages=1)
    print(f"Scraped {len(results)} listings")
    if results:
        print(f"First result: {results[0]}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
