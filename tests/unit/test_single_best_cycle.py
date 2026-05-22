"""Test script for single best opportunity scheduler full cycle.

Tests the full cycle with short durations:
- Scraping: 2 minutes (instead of 45)
- Analysis: 1 minute (instead of 15)
"""
import sys
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.scheduler.single_best_scheduler import SingleBestOpportunityScheduler
from loguru import logger


async def main():
    """Run a short test cycle."""
    logger.info("=" * 60)
    logger.info("TEST: Full Cycle (Short Version)")
    logger.info("Scraping: 2 minutes")
    logger.info("Analysis: 1 minute")
    logger.info("=" * 60)

    scheduler = SingleBestOpportunityScheduler()

    # Run short cycle: 2min scraping + 1min analysis
    await scheduler.run_once(scrape_minutes=2)

    logger.info("=" * 60)
    logger.info("TEST COMPLETED")
    logger.info("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
