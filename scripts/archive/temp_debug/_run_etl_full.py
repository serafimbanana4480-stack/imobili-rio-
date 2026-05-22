"""Run ETL + valuation + scoring on all raw listings in one batch."""
import asyncio
import os
import sys

sys.path.insert(0, ".")
os.environ.setdefault("ENRICH_SKIP_HEAVY", "1")

from loguru import logger

from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.repository import DatabaseRepository


async def main():
    repo = DatabaseRepository()
    raw_count = len(repo.get_raw_listings(limit=100000))
    logger.info(f"Raw listings in DB: {raw_count}")

    etl = PipelineETL()
    processed = await etl.run(batch_size=raw_count + 1000)
    logger.info(f"Clean added/updated: {processed}")

    v = ValuationEngine()
    valued = await v.valuate_batch(batch_size=10000)
    logger.info(f"Valuated: {valued}")

    s = ScoringEngine()
    scored = await s.score_batch(batch_size=10000)
    logger.info(f"Scored: {scored}")


if __name__ == "__main__":
    asyncio.run(main())
