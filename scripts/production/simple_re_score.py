"""Simple script to re-score existing listings with new scoring system."""
import asyncio
import sqlite3
from pathlib import Path
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.repository import DatabaseRepository
from loguru import logger

DB_PATH = Path("data/db/realestate.db")

async def main():
    """Re-score existing listings."""
    # Delete existing scores to force re-scoring
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scores")
    conn.commit()
    conn.close()
    logger.info("Deleted existing scores")
    
    repo = DatabaseRepository()
    scoring_engine = ScoringEngine(repo)
    
    # Run scoring batch
    scored = await scoring_engine.score_batch(batch_size=1000)
    logger.info(f"Re-scored {scored} listings successfully")

if __name__ == "__main__":
    asyncio.run(main())
