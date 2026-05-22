"""Model cache for valuation models.

Provides in-memory caching of trained ML models to avoid
repeated loading from disk and improve prediction throughput.
"""
import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class CacheEntry:
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class ModelCache:
    """Thread-safe in-memory cache for ML models with TTL and LRU eviction."""

    def __init__(self, max_size: int = 10, ttl_seconds: float = 3600.0):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self.misses += 1
                return None

            if entry.age_seconds > self.ttl_seconds:
                del self._cache[key]
                self.evictions += 1
                self.misses += 1
                return None

            entry.touch()
            self.hits += 1
            return entry.value

    def set(self, key: str, value: Any):
        with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = CacheEntry(value=value)

    def get_or_load(self, key: str, loader: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached

        value = loader()
        self.set(key, value)
        return value

    def _evict_lru(self):
        if not self._cache:
            return
        lru_key = min(self._cache, key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self.evictions += 1

    def invalidate(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> Dict:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self.evictions,
            }

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)


_model_cache = ModelCache()


def get_model_cache() -> ModelCache:
    return _model_cache
