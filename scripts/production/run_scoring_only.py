"""Script para executar apenas scoring batch sem scraping."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.repository import DatabaseRepository
from loguru import logger

async def main():
    """Executar scoring batch em listings existentes."""
    repo = DatabaseRepository()
    scoring_engine = ScoringEngine(repo)
    
    logger.info("Iniciando scoring batch...")
    scored = await scoring_engine.score_batch(batch_size=1000)
    logger.info(f"Scored {scored} listings")

if __name__ == "__main__":
    asyncio.run(main())
