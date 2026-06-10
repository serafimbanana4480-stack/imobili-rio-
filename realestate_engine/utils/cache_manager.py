"""Redis cache manager for caching expensive operations.

Caches:
- Geocoding results (address -> coordinates)
- INE API responses (market data)
- Valuation calculations (expensive ML models)
- External API responses
"""
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, UTC, timedelta
from loguru import logger

from realestate_engine.utils.config import config


class CacheManager:
    """Redis cache manager with TTL and statistics."""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self.backend = "disabled"
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Redis."""
        if config.cache_backend == "memory":
            self.enabled = True
            self.backend = "memory"
            logger.info("Memory cache enabled")
            return
        try:
            import redis
            self.redis_client = redis.from_url(
                config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            self.backend = "redis"
            logger.info("Redis cache connected successfully")
        except ImportError:
            self._enable_fallback("Redis not installed")
        except Exception as e:
            if config.redis_required:
                raise RuntimeError(f"Redis connection failed and REDIS_REQUIRED=true: {e}") from e
            self._enable_fallback(f"Redis connection failed: {e}")
    
    def _enable_fallback(self, reason: str) -> None:
        """Enable local memory fallback when Redis is unavailable."""
        if config.cache_backend in {"auto", "memory"}:
            self.enabled = True
            self.backend = "memory"
            logger.warning(f"{reason}, using memory cache fallback")
            return
        self.enabled = False
        self.backend = "disabled"
        logger.warning(f"{reason}, caching disabled")
    
    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self.enabled and (self.backend == "memory" or self.redis_client is not None)
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a cache key with prefix."""
        return f"{prefix}:{identifier}"
    
    def _hash_key(self, data: str) -> str:
        """Generate a hash for data as cache key."""
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, prefix: str, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_enabled():
            return None
        
        try:
            cache_key = self._generate_key(prefix, key)
            if self.backend == "memory":
                item = self._memory_cache.get(cache_key)
                if not item:
                    self.stats["misses"] += 1
                    return None
                expires_at = item.get("expires_at")
                if expires_at and expires_at < datetime.now(UTC):
                    self._memory_cache.pop(cache_key, None)
                    self.stats["misses"] += 1
                    return None
                self.stats["hits"] += 1
                return item.get("value")
            value = self.redis_client.get(cache_key)
            if value is not None:
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, prefix: str, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.is_enabled():
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            if self.backend == "memory":
                self._memory_cache[cache_key] = {
                    "value": value,
                    "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
                }
                self.stats["sets"] += 1
                return True
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(cache_key, ttl_seconds, serialized)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, key: str) -> bool:
        """Delete value from cache."""
        if not self.is_enabled():
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            if self.backend == "memory":
                existed = cache_key in self._memory_cache
                self._memory_cache.pop(cache_key, None)
                if existed:
                    self.stats["deletes"] += 1
                return existed
            self.redis_client.delete(cache_key)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with a prefix."""
        if not self.is_enabled():
            return 0
        
        try:
            pattern = f"{prefix}:*"
            if self.backend == "memory":
                keys = [k for k in self._memory_cache if k.startswith(f"{prefix}:")]
                for key in keys:
                    self._memory_cache.pop(key, None)
                return len(keys)
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear prefix error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total_requests,
            "enabled": self.enabled,
            "backend": self.backend,
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }


# Global cache manager instance
cache_manager = CacheManager()


def cache_geocoding(address: str) -> Optional[Dict[str, Any]]:
    """Cache geocoding results."""
    key = cache_manager._hash_key(address)
    return cache_manager.get("geocoding", key)


def set_geocoding_cache(address: str, result: Dict[str, Any], ttl_hours: int = 24) -> bool:
    """Set geocoding cache."""
    key = cache_manager._hash_key(address)
    return cache_manager.set("geocoding", key, result, ttl_seconds=ttl_hours * 3600)


def cache_ine_data(concelho: str, tipo_imovel: str, ano: int, trimestre: int) -> Optional[Dict[str, Any]]:
    """Cache INE market data."""
    key = f"{concelho}:{tipo_imovel}:{ano}:{trimestre}"
    return cache_manager.get("ine", key)


def set_ine_cache(concelho: str, tipo_imovel: str, ano: int, trimestre: int, 
                   data: Dict[str, Any], ttl_hours: int = 168) -> bool:  # 7 days
    """Set INE cache."""
    key = f"{concelho}:{tipo_imovel}:{ano}:{trimestre}"
    return cache_manager.set("ine", key, data, ttl_seconds=ttl_hours * 3600)


def cache_valuation(listing_id: str, features_hash: str) -> Optional[Dict[str, Any]]:
    """Cache valuation results."""
    key = f"{listing_id}:{features_hash}"
    return cache_manager.get("valuation", key)


def set_valuation_cache(listing_id: str, features_hash: str, 
                        result: Dict[str, Any], ttl_hours: int = 24) -> bool:
    """Set valuation cache."""
    key = f"{listing_id}:{features_hash}"
    return cache_manager.set("valuation", key, result, ttl_seconds=ttl_hours * 3600)


def invalidate_valuation_cache(listing_id: str) -> bool:
    """Invalidate valuation cache for a listing."""
    pattern = f"{listing_id}:*"
    return cache_manager.clear_prefix(f"valuation:{listing_id}") > 0
