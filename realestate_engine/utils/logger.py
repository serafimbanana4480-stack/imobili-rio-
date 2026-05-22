"""Structured logging configuration using Loguru.

Enhanced with:
- Separate log files for different components
- Structured logging with consistent fields
- Performance logging for critical operations
- Error tracking integration
"""
import sys
import os
from loguru import logger
from realestate_engine.utils.config import config


def setup_logging() -> None:
    """Configure Loguru logger with structured output."""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Create log directory structure
    log_dir = os.path.join(config.data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Component-specific log directories
    component_dirs = {
        "scraping": os.path.join(log_dir, "scraping"),
        "etl": os.path.join(log_dir, "etl"),
        "valuation": os.path.join(log_dir, "valuation"),
        "scoring": os.path.join(log_dir, "scoring"),
        "notification": os.path.join(log_dir, "notification"),
        "scheduler": os.path.join(log_dir, "scheduler"),
        "dashboard": os.path.join(log_dir, "dashboard"),
    }
    
    for comp_dir in component_dirs.values():
        os.makedirs(comp_dir, exist_ok=True)
    
    # Main application log with rotation
    logger.add(
        os.path.join(log_dir, "realestate_{time:YYYY-MM-DD}.log"),
        level=config.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Error file handler
    logger.add(
        os.path.join(log_dir, "errors_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Component-specific logs
    logger.add(
        os.path.join(component_dirs["scraping"], "scraping_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "scraping" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["etl"], "etl_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "etl" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["valuation"], "valuation_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "valuation" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["scoring"], "scoring_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "scoring" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["notification"], "notification_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "notification" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["scheduler"], "scheduler_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "scheduler" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    logger.add(
        os.path.join(component_dirs["dashboard"], "dashboard_{time:YYYY-MM-DD}.log"),
        level="INFO",
        filter=lambda record: "dashboard" in record["name"].lower(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )


def log_performance(operation: str, duration_ms: float, **context):
    """Log performance metrics for critical operations."""
    logger.info(f"PERFORMANCE | {operation} | {duration_ms:.2f}ms | {context}")


def log_error_with_context(error_type: str, error: Exception, **context):
    """Log error with structured context for tracking."""
    logger.error(f"ERROR | {error_type} | {str(error)} | context={context}")


setup_logging()
