"""Main entry point for Real Estate Opportunity Engine."""
import asyncio
import sys
from loguru import logger

from realestate_engine.utils.config import config
from realestate_engine.utils.logger import setup_logging
from realestate_engine.database.models import init_db
from realestate_engine.scheduler.orchestrator import Orchestrator
from realestate_engine.monitoring.metrics import MetricsCollector


def initialize():
    """Initialize system components."""
    setup_logging()
    logger.info("Initializing Real Estate Opportunity Engine")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Start metrics server
    metrics = MetricsCollector()
    try:
        metrics.start_server()
    except Exception as e:
        logger.warning(f"Metrics server not started: {e}")
    
    logger.info("Initialization complete")


def run_scheduler():
    """Run the scheduler with the orchestrator."""
    orchestrator = Orchestrator()
    
    logger.info("Starting Orchestrator. Press Ctrl+C to stop.")
    
    try:
        asyncio.run(orchestrator.run_forever())
    except KeyboardInterrupt:
        logger.info("Shutting down...")


def main():
    """Main entry point."""
    initialize()
    run_scheduler()


if __name__ == "__main__":
    main()
