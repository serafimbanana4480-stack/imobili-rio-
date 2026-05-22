import asyncio
import sys
sys.path.insert(0, 'realestate_engine')

from realestate_engine.scraping.spiders.casa_sapo_spider_nodriver import CasaSapoSpider

async def test():
    spider = CasaSapoSpider()
    print("Starting spider with visible browser for debugging...")
    results = await spider.run(max_pages=1, headless=False)
    
    print(f"\n{'='*80}")
    print(f"SCRAPED {len(results)} LISTINGS")
    print(f"{'='*80}")
    
    for i, listing in enumerate(results[:3], 1):
        data = listing.get('raw_data', {})
        print(f"\n{i}. Source ID: {data.get('source_id', 'N/A')}")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Price: {data.get('price_text', 'N/A')}")
        print(f"   Area: {data.get('area_text', 'N/A')}")
        print(f"   Rooms: {data.get('rooms_text', 'N/A')}")
        print(f"   URL: {data.get('url', 'N/A')[:80]}")
    
    with_area = sum(1 for l in results if l.get('raw_data', {}).get('area_text'))
    print(f"\n{'='*80}")
    print(f"Listings with area: {with_area}/{len(results)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test())
