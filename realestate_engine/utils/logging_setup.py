"""Logging setup utility for the Real Estate Engine.

Configures loguru with:
- Colored console output for development
- Structured JSON file output for production
- Log rotation and retention
- Separate error log file
"""
import sys
import os
from loguru import logger
from realestate_engine.utils.config import config


def setup_logging():
    """Configure loguru with appropriate handlers based on environment."""
    # Remove default handler
    logger.remove()

    # Console handler — colored for dev, plain for prod
    if config.json_logs:
        logger.add(
            sys.stderr,
            format=(
                '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
                '"level": "{level}", '
                '"name": "{name}", '
                '"function": "{function}", '
                '"line": {line}, '
                '"message": "{message}"}'
            ),
            level=config.log_level,
            colorize=False,
        )
    else:
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level=config.log_level,
            colorize=True,
        )

    # Ensure log directory exists
    os.makedirs("logs", exist_ok=True)

    # File handler — always structured JSON for machine readability
    logger.add(
        "logs/engine.log",
        format=(
            '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"name": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"}'
        ),
        level="DEBUG",
        rotation=config.log_rotation_size,
        retention=f"{config.log_retention_days} days",
        compression="gz",
    )

    # Error file — separate for alerting
    logger.add(
        "logs/errors.log",
        format=(
            '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"name": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}", '
            '"exception": "{exception}"}'
        ),
        level="ERROR",
        rotation=config.log_rotation_size,
        retention=f"{config.log_retention_days * 2} days",
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging configured — level={config.log_level}, json={config.json_logs}")
