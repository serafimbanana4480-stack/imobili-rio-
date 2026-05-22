"""Quick end-to-end test: scrape 3 portals (1 page each) → save raw → show DB delta.

Does NOT run ETL/valuation/scoring (those are slow). Only tests the scraping
layer + DB persistence that was the user's main concern.
"""
import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.scraping.spider_manager import SpiderManager

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

async def main():
    repo = DatabaseRepository()
    repo.init_tables()

    import sqlite3
    db = sqlite3.connect("data/db/realestate.db")
    cur = db.cursor()
    before = cur.execute("SELECT source_portal, COUNT(*) FROM raw_listings GROUP BY source_portal").fetchall()
    before_dict = {r[0]: r[1] for r in before}
    print(f"\n=== BEFORE ===")
    for p, c in before_dict.items():
        print(f"  {p}: {c}")
    total_before = sum(before_dict.values())
    print(f"  TOTAL: {total_before}")

    mgr = SpiderManager()
    portals = [("imovirtual", 1), ("casa_sapo", 1), ("remax", 1)]

    for portal, pages in portals:
        print(f"\n--- Scraping {portal} (max_pages={pages}) ---")
        try:
            results = await mgr.run_spider(portal, max_pages=pages, headless=True)
            print(f"  → {len(results)} raw listings saved")
        except Exception as e:
            print(f"  → FAILED: {type(e).__name__}: {e}")

    after = cur.execute("SELECT source_portal, COUNT(*) FROM raw_listings GROUP BY source_portal").fetchall()
    after_dict = {r[0]: r[1] for r in after}
    total_after = sum(after_dict.values())

    print(f"\n=== AFTER ===")
    for p, c in after_dict.items():
        delta = c - before_dict.get(p, 0)
        print(f"  {p}: {c} (+{delta})")
    print(f"  TOTAL: {total_after} (+{total_after - total_before})")

    # Show sample records from new portals
    for portal in ("casa_sapo", "remax"):
        rows = cur.execute(
            f"SELECT source_id, source_url, scrape_timestamp FROM raw_listings WHERE source_portal=? ORDER BY id DESC LIMIT 3",
            (portal,)
        ).fetchall()
        if rows:
            print(f"\n--- Sample {portal} records ---")
            for r in rows:
                print(f"  id={r[0]} | {r[1][:80]}... | {r[2][:19]}")

if __name__ == "__main__":
    asyncio.run(main())
