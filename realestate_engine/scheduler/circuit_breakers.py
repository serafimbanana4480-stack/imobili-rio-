"""Circuit breaker pattern for Real Estate Opportunity Engine."""
import time
import threading
from typing import Optional, Callable, Any
from enum import Enum
from loguru import logger


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    def can_execute(self) -> bool:
        """Check if operation can execute."""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit breaker {self.name}: transitioning to HALF_OPEN")
                    return True
                logger.warning(f"Circuit breaker {self.name}: OPEN, blocking call")
                return False
            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        return False
    
    def record_success(self):
        """Record successful execution."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker {self.name}: CLOSED")
            else:
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self):
        """Record failed execution."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name}: OPEN (failure in HALF_OPEN)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name}: OPEN ({self._failure_count} failures)")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self.can_execute():
            raise Exception(f"Circuit breaker {self.name} is OPEN")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class CircuitBreakerRegistry:
    """Registry of circuit breakers."""
    
    def __init__(self):
        self._breakers: dict = {}
    
    def get(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, **kwargs)
        return self._breakers[name]
    
    def health(self) -> dict:
        """Get health status of all circuit breakers."""
        return {name: cb.state.value for name, cb in self._breakers.items()}
