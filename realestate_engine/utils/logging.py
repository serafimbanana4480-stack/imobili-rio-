"""Structured logging helpers for consistent log formatting."""

from typing import Optional, Dict
from loguru import logger


class StructuredLogger:
    """Logger wrapper with structured context for consistent log formatting."""

    def __init__(self, name: str, context: Optional[Dict] = None):
        self._logger = logger.bind(name=name, **(context or {}))

    def info(self, message: str, **kwargs):
        self._logger.info(message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        self._logger.error(message, exc_info=exc_info, **kwargs)

    def warning(self, message: str, **kwargs):
        self._logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._logger.debug(message, **kwargs)

    def exception(self, message: str, **kwargs):
        self._logger.exception(message, **kwargs)
