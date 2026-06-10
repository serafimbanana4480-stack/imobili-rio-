"""Enhanced logging utilities with correlation IDs and structured logging."""
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from functools import wraps
from loguru import logger

# Context variable for correlation ID (request/operation tracking)
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class LoggingUtils:
    """Enhanced logging utilities."""

    @staticmethod
    def get_correlation_id() -> str:
        """Get or create correlation ID for current operation."""
        cid = correlation_id.get()
        if cid is None:
            cid = str(uuid.uuid4())
            correlation_id.set(cid)
        return cid

    @staticmethod
    def set_correlation_id(cid: str):
        """Set correlation ID for current operation."""
        correlation_id.set(cid)

    @staticmethod
    def clear_correlation_id():
        """Clear correlation ID."""
        correlation_id.set(None)

    @staticmethod
    def log_with_context(message: str, **kwargs):
        """Log message with correlation ID and additional context."""
        cid = LoggingUtils.get_correlation_id()
        log_data = {"correlation_id": cid, **kwargs}
        logger.bind(**log_data).info(message)

    @staticmethod
    def log_error_with_context(message: str, **kwargs):
        """Log error with correlation ID and additional context."""
        cid = LoggingUtils.get_correlation_id()
        log_data = {"correlation_id": cid, **kwargs}
        logger.bind(**log_data).error(message)


def with_logging(operation_name: str, log_args: bool = False, log_result: bool = False):
    """Decorator to add automatic logging to functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cid = LoggingUtils.get_correlation_id()
            logger.bind(correlation_id=cid, operation=operation_name).debug(f"Starting {operation_name}")
            
            if log_args:
                logger.bind(correlation_id=cid).debug(f"Args: {args[:2] if args else 'None'}..., Kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_result:
                    logger.bind(correlation_id=cid).debug(f"Result: {result}")
                
                logger.bind(correlation_id=cid, operation=operation_name).info(f"Completed {operation_name}")
                return result
                
            except Exception as e:
                logger.bind(correlation_id=cid, operation=operation_name).error(f"Failed {operation_name}: {e}")
                raise
                
        return wrapper
    return decorator


def with_async_logging(operation_name: str, log_args: bool = False, log_result: bool = False):
    """Decorator to add automatic logging to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cid = LoggingUtils.get_correlation_id()
            logger.bind(correlation_id=cid, operation=operation_name).debug(f"Starting {operation_name}")
            
            if log_args:
                logger.bind(correlation_id=cid).debug(f"Args: {args[:2] if args else 'None'}..., Kwargs: {kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                
                if log_result:
                    logger.bind(correlation_id=cid).debug(f"Result: {result}")
                
                logger.bind(correlation_id=cid, operation=operation_name).info(f"Completed {operation_name}")
                return result
                
            except Exception as e:
                logger.bind(correlation_id=cid, operation=operation_name).error(f"Failed {operation_name}: {e}")
                raise
                
        return wrapper
    return decorator


class OperationLogger:
    """Context manager for logging operations with automatic timing."""

    def __init__(self, operation_name: str, **context):
        self.operation_name = operation_name
        self.context = context
        self.cid = None
        self.start_time = None

    def __enter__(self):
        self.cid = LoggingUtils.get_correlation_id()
        self.start_time = logger._start_time if hasattr(logger, '_start_time') else None
        
        log_data = {"correlation_id": self.cid, "operation": self.operation_name, **self.context}
        logger.bind(**log_data).info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            log_data = {"correlation_id": self.cid, "operation": self.operation_name}
            logger.bind(**log_data).info(f"Completed: {self.operation_name}")
        else:
            log_data = {"correlation_id": self.cid, "operation": self.operation_name, "error": str(exc_val)}
            logger.bind(**log_data).error(f"Failed: {self.operation_name}")
        return False
