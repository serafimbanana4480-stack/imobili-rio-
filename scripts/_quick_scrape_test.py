"""Quick live test of activated spiders (imovirtual/era/remax/casa_sapo).

Runs with max_pages=1 to keep it short. Reports per-portal item counts.
Does NOT persist to DB — just prints what each spider produced.
"""
import asyncio, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from loguru import logger

from realestate_engine.scraping.proxy_manager import ProxyManager

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

SPIDERS = [
    ("imovirtual", "realestate_engine.scraping.spiders.imovirtual_nextdata_spider", "ImovirtualNextDataSpider"),
    ("era",        "realestate_engine.scraping.spiders.era_spider_nodriver",        "ERASpider"),
    ("remax",      "realestate_engine.scraping.spiders.remax_spider_nodriver",      "REMAXSpider"),
    ("casa_sapo",  "realestate_engine.scraping.spiders.casa_sapo_spider_nodriver",  "CasaSapoSpider"),
]

async def run_one(name, mod_path, cls_name, mgr):
    import importlib
    try:
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
    except Exception as e:
        return (name, 0, 0.0, f"import_fail:{e}")

    spider = cls(proxy_manager=mgr)
    start = time.perf_counter()
    try:
        results = await asyncio.wait_for(spider.run(max_pages=1, headless=True), timeout=180.0)
    except asyncio.TimeoutError:
        return (name, 0, time.perf_counter()-start, "timeout")
    except Exception as e:
        return (name, 0, time.perf_counter()-start, f"run_fail:{type(e).__name__}:{e}")
    return (name, len(results), time.perf_counter()-start, "ok")

async def main():
    mgr = ProxyManager(load_cache=False)
    print(f"ProxyManager: {len(mgr.entries)} entries")
    summary = []
    for name, mod, cls in SPIDERS:
        logger.info(f"=== running spider: {name} ===")
        res = await run_one(name, mod, cls, mgr)
        summary.append(res)
        logger.info(f"{name}: items={res[1]} elapsed={res[2]:.1f}s status={res[3]}")

    print("\n=== SUMMARY ===")
    print(f"{'portal':12s} {'items':>6s} {'time':>7s}  status")
    for name, n, t, status in summary:
        print(f"{name:12s} {n:6d} {t:6.1f}s  {status}")

if __name__ == "__main__":
    asyncio.run(main())
