"""Cache module for query optimization."""
from realestate_engine.cache.redis_cache import RedisCache, redis_cache

__all__ = ["RedisCache", "redis_cache"]
