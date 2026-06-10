import asyncio
import os
from loguru import logger

# ── Configure Logging ────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
# Save all debug logs to engine.log (rotates every 10MB to save space)
logger.add("logs/engine.log", rotation="10 MB", retention="10 days", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
# Save only errors to errors.log, with full stack traces and variable states
logger.add("logs/errors.log", rotation="5 MB", retention="30 days", level="ERROR", backtrace=True, diagnose=True)

from realestate_engine.scheduler.orchestrator import Orchestrator

async def main():
    logger.info("Initializing Real Estate Opportunity Engine (Enterprise v3.0)...")
    logger.info("Starting 24/7 Background Orchestrator.")
    
    orchestrator = Orchestrator()
    
    try:
        # We can trigger an immediate cycle on boot so the user doesn't have to wait for the exact hour
        logger.info("Running initial boot cycle...")
        await orchestrator.run_full_pipeline()
        
        # Start the continuous 24/7 scheduler
        await orchestrator.run_forever()
    except KeyboardInterrupt:
        logger.info("Engine shutdown requested by user. Exiting safely...")

if __name__ == "__main__":
    asyncio.run(main())
