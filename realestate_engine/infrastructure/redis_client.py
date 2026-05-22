"""Shared Redis client used as cache + per-portal rate limiter.

No-op gracefully when Redis is unreachable, unless REDIS_REQUIRED=true.
This module must NEVER fabricate data — on failure it returns cache-miss
(None/False), so callers always fall back to the real upstream source.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from loguru import logger

from realestate_engine.utils.config import config

try:
    import redis  # type: ignore
    _REDIS_LIB_AVAILABLE = True
except Exception:  # pragma: no cover
    redis = None  # type: ignore
    _REDIS_LIB_AVAILABLE = False


class RedisCache:
    """Thin wrapper exposing the operations the engine actually needs."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or config.redis_url
        self._client = None
        self._healthy = False
        if not _REDIS_LIB_AVAILABLE:
            logger.warning("redis-py not installed — RedisCache running in no-op mode")
            return
        try:
            self._client = redis.Redis.from_url(
                self.url, socket_connect_timeout=2, socket_timeout=2,
                decode_responses=True,
            )
            self._client.ping()
            self._healthy = True
            logger.info(f"RedisCache connected: {self.url}")
        except Exception as e:
            if config.redis_required:
                raise RuntimeError(f"Redis is required but unreachable at {self.url}: {e}")
            logger.warning(f"Redis unreachable at {self.url} ({e}); running in no-op mode")
            self._client = None

    # ── Key/value cache ────────────────────────────────────────────────
    def get_json(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.debug(f"Redis get_json({key}) failed: {e}")
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.debug(f"Redis set_json({key}) failed: {e}")
            return False

    # ── Rate limiter (fixed-window) ────────────────────────────────────
    def allow_request(self, bucket: str, max_per_minute: int) -> bool:
        """Return True if the request can proceed under the bucket's budget.

        If Redis is down we fall open (True) to avoid blocking production
        flows, but we log loudly so it is observable.
        """
        if not self._client:
            return True
        window = int(time.time() // 60)
        key = f"ratelimit:{bucket}:{window}"
        try:
            count = self._client.incr(key)
            if count == 1:
                self._client.expire(key, 65)
            if count > max_per_minute:
                logger.warning(f"Rate limit hit for {bucket}: {count}/{max_per_minute}/min")
                return False
            return True
        except Exception as e:
            logger.warning(f"Redis allow_request({bucket}) failed, falling open: {e}")
            return True

    def healthy(self) -> bool:
        return self._healthy


_default_cache: Optional[RedisCache] = None


def get_redis() -> RedisCache:
    """Process-wide singleton."""
    global _default_cache
    if _default_cache is None:
        _default_cache = RedisCache()
    return _default_cache
