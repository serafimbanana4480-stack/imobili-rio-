"""Redis cache for query optimization."""
import os
import pickle
from typing import Any, Optional
import redis
from loguru import logger


class RedisCache:
    """Cache distribuído usando Redis."""
    
    def __init__(self):
        self.redis_client = None
        self.available = False
        self._checked = False
        self._redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    def _ensure_connection(self):
        """Lazy connection to Redis - only connect when first used."""
        if self._checked:
            return
        self._checked = True
        try:
            self.redis_client = redis.from_url(self._redis_url, decode_responses=False, socket_connect_timeout=2, socket_timeout=2)
            self.redis_client.ping()
            self.available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.debug(f"Redis not available (cache disabled): {e}")
            self.redis_client = None
            self.available = False
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do Redis."""
        self._ensure_connection()
        if not self.available:
            return None
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception as e:
            logger.debug(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Define valor no Redis."""
        self._ensure_connection()
        if not self.available:
            return
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.debug(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """Remove chave do Redis."""
        self._ensure_connection()
        if not self.available:
            return
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Remove todas as chaves que combinam com pattern."""
        self._ensure_connection()
        if not self.available:
            return
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.debug(f"Redis clear_pattern error: {e}")


# Singleton global
redis_cache = RedisCache()
