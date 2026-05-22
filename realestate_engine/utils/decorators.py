"""Utility decorators for the Real Estate Opportunity Engine."""
import functools
import time
import asyncio
from typing import Callable, Any, Optional
from loguru import logger
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying a function with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            return None
        return wrapper
    return decorator


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Async decorator for retrying a coroutine with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Async function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            return None
        return wrapper
    return decorator


def timed(func: Callable) -> Callable:
    """Decorator to measure execution time and record metrics."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            metrics.record_latency(func.__name__, elapsed)
            logger.debug(f"{func.__name__} executed in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            metrics.record_error(func.__name__)
            logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
            raise
    return wrapper


def async_timed(func: Callable) -> Callable:
    """Async decorator to measure execution time."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            metrics.record_latency(func.__name__, elapsed)
            logger.debug(f"{func.__name__} executed in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            metrics.record_error(func.__name__)
            logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
            raise
    return wrapper


def circuit_breaker(threshold: int = 5, timeout: float = 60.0):
    """Simple circuit breaker decorator."""
    failures = 0
    last_failure_time: Optional[float] = None
    lock = asyncio.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure_time
            
            async with lock:
                if failures >= threshold:
                    if last_failure_time and (time.time() - last_failure_time) < timeout:
                        raise Exception(f"Circuit breaker open for {func.__name__}")
                    failures = 0
            
            try:
                result = await func(*args, **kwargs)
                async with lock:
                    failures = 0
                return result
            except Exception as e:
                async with lock:
                    failures += 1
                    last_failure_time = time.time()
                raise
        return wrapper
    return decorator
