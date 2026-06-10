"""Script para re-treinar modelos de valuation com novas features."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.database.repository import DatabaseRepository
from loguru import logger

async def main():
    """Re-treinar modelos de valuation."""
    repo = DatabaseRepository()
    valuation_engine = ValuationEngine(repo)
    
    logger.info("Iniciando re-treino de modelos...")
    valuated = await valuation_engine.valuate_batch(batch_size=1000)
    logger.info(f"Avaliados e re-treinados {valuated} listings")

if __name__ == "__main__":
    asyncio.run(main())
