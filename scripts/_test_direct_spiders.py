"""Live test of the two new direct-fetch spiders.

Runs casa_sapo_direct + remax_direct with small budgets.
Prints per-portal stats and the first 3 listing records.
"""
import asyncio, sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from loguru import logger
from realestate_engine.scraping.proxy_manager import ProxyManager
from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider
from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

async def main():
    mgr = ProxyManager(load_cache=False)

    for cls, max_pages in [(CasaSapoDirectSpider, 2), (REMAXDirectSpider, 1)]:
        spider = cls(proxy_manager=mgr)
        logger.info(f"=== testing {spider.name} ===")
        results = await spider.run(max_pages=max_pages)
        logger.info(f"{spider.name}: {len(results)} listings, stats={spider.stats}")
        for r in results[:3]:
            rd = r["raw_data"]
            print(f"  id={r['source_id']:>12s} | {rd.get('rooms_text','?'):4s} | "
                  f"{rd.get('area_text','?'):7s} | {rd.get('price_text','?'):>14s} | "
                  f"{rd.get('location','?')[:30]:30s} | {r['source_url'][:60]}")

asyncio.run(main())
