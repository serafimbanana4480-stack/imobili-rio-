"""Utility decorators for the Real Estate Opportunity Engine.

Provides retry with jitter, circuit breaker, and latency metrics.
"""
import functools
import random
import time
import asyncio
import threading
from typing import Callable, Any, Tuple, Type
from loguru import logger
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()


def _jitter(delay: float, factor: float = 0.1) -> float:
    """Add +/- factor% random jitter to a delay value."""
    return delay * (1.0 + random.uniform(-factor, factor))


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (ConnectionError, TimeoutError),
):
    """Decorator: retry a sync function with exponential backoff + optional jitter."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if isinstance(exc, (KeyboardInterrupt, SystemExit, GeneratorExit)):
                        raise
                    if attempt >= max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {exc}")
                        raise
                    wait = _jitter(current_delay) if jitter else current_delay
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {exc}. Retrying in {wait:.2f}s...")
                    time.sleep(wait)
                    current_delay *= backoff
                    attempt += 1
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (ConnectionError, TimeoutError),
):
    """Decorator: retry an async function with exponential backoff + optional jitter."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if isinstance(exc, (KeyboardInterrupt, SystemExit, GeneratorExit)):
                        raise
                    if attempt >= max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {exc}")
                        raise
                    wait = _jitter(current_delay) if jitter else current_delay
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {exc}. Retrying in {wait:.2f}s...")
                    await asyncio.sleep(wait)
                    current_delay *= backoff
                    attempt += 1
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


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open and rejecting calls."""
    pass


def circuit_breaker(threshold: int = 5, recovery_timeout: float = 60.0, half_open_attempts: int = 1):
    """Decorator: sync circuit breaker.

    State machine: CLOSED → (failures >= threshold) → OPEN → (timeout) → HALF_OPEN → CLOSED
    """
    state = {"failures": 0, "last_failure": 0.0, "open": False, "half_open_remaining": 0}
    lock = threading.Lock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with lock:
                if state["open"]:
                    elapsed = time.time() - state["last_failure"]
                    if elapsed >= recovery_timeout:
                        state["open"] = False
                        state["half_open_remaining"] = half_open_attempts
                        logger.info(f"Circuit breaker for {func.__name__} → HALF_OPEN")
                    else:
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker open for {func.__name__} (retry in {recovery_timeout - elapsed:.0f}s)"
                        )

            try:
                result = func(*args, **kwargs)
                with lock:
                    state["failures"] = 0
                    state["half_open_remaining"] = 0
                return result
            except Exception:
                with lock:
                    state["failures"] += 1
                    state["last_failure"] = time.time()
                    if state["half_open_remaining"] > 0:
                        state["half_open_remaining"] -= 1
                    if state["failures"] >= threshold and state["half_open_remaining"] <= 0:
                        state["open"] = True
                        logger.warning(f"Circuit breaker OPEN for {func.__name__}")
                raise
        return wrapper
    return decorator


def async_circuit_breaker(threshold: int = 5, recovery_timeout: float = 60.0, half_open_attempts: int = 1):
    """Decorator: async circuit breaker with proper state machine."""
    state = {"failures": 0, "last_failure": 0.0, "open": False, "half_open_remaining": 0}
    lock = asyncio.Lock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            async with lock:
                if state["open"]:
                    elapsed = time.time() - state["last_failure"]
                    if elapsed >= recovery_timeout:
                        state["open"] = False
                        state["half_open_remaining"] = half_open_attempts
                        logger.info(f"Circuit breaker for {func.__name__} → HALF_OPEN")
                    else:
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker open for {func.__name__} (retry in {recovery_timeout - elapsed:.0f}s)"
                        )

            try:
                result = await func(*args, **kwargs)
                async with lock:
                    state["failures"] = 0
                    state["half_open_remaining"] = 0
                return result
            except Exception:
                async with lock:
                    state["failures"] += 1
                    state["last_failure"] = time.time()
                    if state["half_open_remaining"] > 0:
                        state["half_open_remaining"] -= 1
                    if state["failures"] >= threshold and state["half_open_remaining"] <= 0:
                        state["open"] = True
                        logger.warning(f"Circuit breaker OPEN for {func.__name__}")
                raise
        return wrapper
    return decorator
