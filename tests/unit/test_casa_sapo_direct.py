"""Test Casa Sapo Direct spider standalone."""
import asyncio
import sys
sys.path.insert(0, '.')

from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider

async def main():
    spider = CasaSapoDirectSpider()
    print("Testing Casa Sapo Direct spider with max_pages=1...")
    results = await spider.run(max_pages=1)
    print(f"Scraped {len(results)} listings")
    if results:
        print(f"First result: {results[0]}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
