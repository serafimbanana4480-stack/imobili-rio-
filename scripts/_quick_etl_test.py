"""Quick ETL + Valuation + Scoring test on newly scraped data."""
import asyncio, sys, pathlib, sqlite3
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

async def main():
    db = sqlite3.connect("data/db/realestate.db")
    cur = db.cursor()

    def counts(label):
        print(f"\n=== {label} ===")
        for t in ["raw_listings","clean_listings","valuations","scores"]:
            c = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:20s}: {c}")
        portals = cur.execute("SELECT source_portal, COUNT(*) FROM raw_listings GROUP BY source_portal").fetchall()
        for p, c in portals:
            print(f"  raw [{p}]: {c}")

    counts("BEFORE")

    from realestate_engine.etl.pipeline_etl import PipelineETL
    etl = PipelineETL()
    processed = await etl.run(batch_size=500)
    print(f"\n→ ETL processed: {processed}")

    from realestate_engine.valuation.valuation_engine import ValuationEngine
    val = ValuationEngine()
    valuated = await val.valuate_batch(batch_size=500)
    print(f"→ Valuated: {valuated}")

    from realestate_engine.scoring.scoring_engine import ScoringEngine
    scoring = ScoringEngine()
    scored = await scoring.score_batch(batch_size=500)
    print(f"→ Scored: {scored}")

    counts("AFTER")

    # Show top scores from new portals
    print("\n--- Top 5 scores (new data) ---")
    rows = cur.execute("""
        SELECT s.total_score, c.source_portal, c.source_id, c.preco_pedido, c.area_util_m2, c.quartos
        FROM scores s JOIN clean_listings c ON s.listing_id = c.id
        ORDER BY s.total_score DESC LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"  score={r[0]:.1f} | {r[1]}:{r[2]} | €{r[3]:,.0f} | {r[4]}m² | T{r[5]}")

if __name__ == "__main__":
    asyncio.run(main())
