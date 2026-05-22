"""Proxy management for professional residential rotation (2026 Standard).

Extended with:
- Free-proxy discovery + validation (``refresh_free_pool``).
- Rotation strategies (random / round-robin / health-score).
- Persistent JSON cache (``data/cache/proxy_pool.json``).
- Per-portal hybrid policy (direct / proxy-required / proxy-fallback).

Backward compatible: the original ``get_proxy()``, ``mark_success``,
``mark_failed`` API continues to work exactly as before. New
capabilities are additive.
"""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from realestate_engine.utils.config import config


# --- Portal strategy table ----------------------------------------------
# How each portal should be scraped.
#
#   "direct"   — never use a proxy (portal does not block direct IPs).
#   "proxy"    — always use a proxy; skip if none available.
#   "hybrid"   — try direct first; retry via proxy on block/ban.
PORTAL_STRATEGY: Dict[str, str] = {
    "imovirtual": "direct",
    "casa_sapo":  "hybrid",
    "era":        "hybrid",
    "remax":      "hybrid",
    "century21":  "hybrid",
    "supercasa":  "hybrid",
    "olx":        "proxy",
    "idealista":  "proxy",
}


CACHE_FILE = Path(config.cache_dir) / "proxy_pool.json"
CACHE_TTL_SECONDS = 6 * 3600  # 6h


@dataclass
class ProxyEntry:
    """Richer proxy record used by the rotating pool."""
    url: str
    source: str = "manual"
    success: int = 0
    failure: int = 0
    last_used: float = 0.0
    latency_ms: float = 0.0
    quarantined_until: float = 0.0  # epoch; 0 means not quarantined

    def score(self) -> float:
        total = self.success + self.failure
        success_rate = (self.success / total) if total else 0.5
        # Favour lower latency (cap at 10s for scoring purposes).
        latency_penalty = min(self.latency_ms, 10000.0) / 10000.0
        recency_bonus = 1.0 if (time.time() - self.last_used) > 60 else 0.5
        return (success_rate * (1.0 - 0.3 * latency_penalty)) * recency_bonus

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "source": self.source,
            "success": self.success,
            "failure": self.failure,
            "last_used": self.last_used,
            "latency_ms": self.latency_ms,
            "quarantined_until": self.quarantined_until,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyEntry":
        return cls(
            url=data["url"],
            source=data.get("source", "cache"),
            success=int(data.get("success", 0)),
            failure=int(data.get("failure", 0)),
            last_used=float(data.get("last_used", 0.0)),
            latency_ms=float(data.get("latency_ms", 0.0)),
            quarantined_until=float(data.get("quarantined_until", 0.0)),
        )


class ProxyManager:
    """Manages proxy rotation with health checks and intelligent fallback.

    Three-tier priority when serving ``get_proxy()``:
      1. Primary residential proxy (env ``RESIDENTIAL_PROXY_URL``).
      2. User-supplied pool (env ``PROXY_LIST`` / ``PROXY_POOL``).
      3. Free-proxy pool (loaded from disk cache or refreshed on demand).
    """

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        proxy_pool: Optional[List[str]] = None,
        rotation_strategy: str = "health",  # health | random | round_robin
        load_cache: bool = True,
    ):
        self.primary_proxy = proxy_url or config.residential_proxy_url or None
        self.rotation_strategy = rotation_strategy
        self._rr_cursor = 0

        # Manually supplied pool (env or constructor).
        raw_pool = os.getenv("PROXY_POOL", "")
        manual = proxy_pool or (
            [p.strip() for p in raw_pool.split(",") if p.strip()] if raw_pool else []
        )
        if getattr(config, "proxy_list", None):
            manual += list(config.proxy_list)

        self.entries: Dict[str, ProxyEntry] = {}
        if self.primary_proxy:
            self.entries[self.primary_proxy] = ProxyEntry(
                url=self.primary_proxy, source="primary"
            )
        for url in manual:
            if url and url not in self.entries:
                self.entries[url] = ProxyEntry(url=url, source="manual")

        self.failed_proxies: set = set()  # kept for backward compat
        self.proxy_stats: Dict[str, Dict] = {}  # kept for backward compat
        self.last_health_check: float = 0.0

        if load_cache:
            self._load_cache()

        logger.info(
            f"ProxyManager initialized: {len(self.entries)} entries "
            f"(primary={'yes' if self.primary_proxy else 'no'}, "
            f"manual={len(manual)}, cached={len(self.entries) - (1 if self.primary_proxy else 0) - len(manual)}), "
            f"strategy={self.rotation_strategy}"
        )

    # ------------------------------------------------------------------ #
    # Backward-compatible properties / legacy fields                     #
    # ------------------------------------------------------------------ #
    @property
    def proxy_pool(self) -> List[str]:
        """Legacy list-of-URLs view."""
        return [e.url for e in self.entries.values()]

    @property
    def proxy_url(self) -> Optional[str]:
        return self.primary_proxy

    @property
    def get_proxy_health(self) -> Dict[str, Dict]:
        return {
            "total": len(self.entries),
            "failed": sum(1 for e in self.entries.values() if self._is_quarantined(e)),
            "healthy": sum(1 for e in self.entries.values() if not self._is_quarantined(e)),
            "stats": {e.url: {"success": e.success, "failure": e.failure,
                              "latency_ms": e.latency_ms, "last_used": e.last_used}
                      for e in self.entries.values()},
        }

    # ------------------------------------------------------------------ #
    # Core API                                                           #
    # ------------------------------------------------------------------ #
    def get_proxy(self, portal: Optional[str] = None) -> Optional[str]:
        """Return the best available proxy URL, or ``None`` for direct."""
        # Honour per-portal strategy.
        if portal:
            strategy = PORTAL_STRATEGY.get(portal, "hybrid")
            if strategy == "direct":
                return None

        candidates = [e for e in self.entries.values() if not self._is_quarantined(e)]
        if not candidates:
            if self.primary_proxy:
                logger.debug("ProxyManager: all proxies quarantined, falling back to primary")
                return self.primary_proxy
            logger.warning("ProxyManager: no usable proxies — returning None (direct)")
            return None

        if self.rotation_strategy == "random":
            chosen = random.choice(candidates)
        elif self.rotation_strategy == "round_robin":
            chosen = candidates[self._rr_cursor % len(candidates)]
            self._rr_cursor += 1
        else:  # "health" (default)
            chosen = max(candidates, key=lambda e: e.score())

        chosen.last_used = time.time()
        return chosen.url

    def mark_success(self, proxy: str, latency_ms: float = 0.0) -> None:
        entry = self.entries.get(proxy)
        if entry is None:
            entry = self.entries.setdefault(proxy, ProxyEntry(url=proxy, source="runtime"))
        entry.success += 1
        if latency_ms:
            entry.latency_ms = 0.7 * entry.latency_ms + 0.3 * latency_ms if entry.latency_ms else latency_ms
        entry.quarantined_until = 0.0
        # Legacy mirror
        self.failed_proxies.discard(proxy)

    def mark_failed(self, proxy: str, error: Optional[str] = None) -> None:
        entry = self.entries.get(proxy)
        if entry is None:
            entry = self.entries.setdefault(proxy, ProxyEntry(url=proxy, source="runtime"))
        entry.failure += 1
        # Exponential quarantine: 2^failures minutes, capped at 60 min.
        backoff_min = min(2 ** entry.failure, 60)
        entry.quarantined_until = time.time() + backoff_min * 60
        # Legacy mirror
        self.failed_proxies.add(proxy)
        logger.debug(f"Proxy failed (quarantined {backoff_min}min): {proxy[:60]} — {error or 'unknown'}")

    def _is_quarantined(self, entry: ProxyEntry) -> bool:
        return entry.quarantined_until > time.time()

    async def refresh_proxies(self) -> None:
        """Async-friendly auto-recovery of stale quarantined proxies."""
        now = time.time()
        if now - self.last_health_check < 60:
            return
        self.last_health_check = now
        recovered = 0
        for entry in self.entries.values():
            if 0 < entry.quarantined_until <= now:
                entry.quarantined_until = 0.0
                recovered += 1
        if recovered:
            logger.info(f"ProxyManager: auto-recovered {recovered} proxies")

    def reset_failures(self) -> None:
        for e in self.entries.values():
            e.failure = 0
            e.quarantined_until = 0.0
        self.failed_proxies.clear()
        logger.info("ProxyManager: all failure counters cleared")

    # ------------------------------------------------------------------ #
    # Free-proxy integration (new)                                       #
    # ------------------------------------------------------------------ #
    async def refresh_free_pool(
        self,
        target_url: Optional[str] = None,
        max_validate: int = 400,
        max_accept: int = 50,
    ) -> int:
        """Fetch, validate, and load free proxies into the active pool.

        Returns the number of proxies added to the active pool.
        """
        # Import locally to keep ProxyManager importable without network deps.
        from realestate_engine.scraping.free_proxy_provider import FreeProxyProvider
        from realestate_engine.scraping.proxy_validator import ProxyValidator

        provider = FreeProxyProvider()
        raw = await provider.fetch_all()
        if not raw:
            logger.warning("ProxyManager.refresh_free_pool: no raw proxies fetched")
            return 0

        sample = raw[:max_validate]
        logger.info(
            f"ProxyManager.refresh_free_pool: validating {len(sample)}/{len(raw)} raw proxies"
        )
        validator = ProxyValidator(target_url=target_url, max_concurrent=40)
        pool = await validator.validate_batch(sample)

        usable = pool.usable()[:max_accept]
        added = 0
        for check in usable:
            url = check.proxy.url
            if url in self.entries:
                continue
            self.entries[url] = ProxyEntry(
                url=url,
                source=f"free:{check.proxy.source}",
                latency_ms=check.latency_ms,
                success=1,  # survived validation = one successful interaction
            )
            added += 1

        self._save_cache()
        logger.info(
            f"ProxyManager.refresh_free_pool: added {added} validated proxies "
            f"(pool now={len(self.entries)})"
        )
        return added

    # ------------------------------------------------------------------ #
    # Persistent cache                                                   #
    # ------------------------------------------------------------------ #
    def _load_cache(self) -> None:
        try:
            if not CACHE_FILE.exists():
                return
            age = time.time() - CACHE_FILE.stat().st_mtime
            if age > CACHE_TTL_SECONDS:
                logger.info(f"ProxyManager: cache stale ({age/3600:.1f}h), ignoring")
                return
            raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            loaded = 0
            for item in raw.get("entries", []):
                try:
                    entry = ProxyEntry.from_dict(item)
                except Exception:
                    continue
                if entry.url not in self.entries:
                    self.entries[entry.url] = entry
                    loaded += 1
            logger.info(f"ProxyManager: loaded {loaded} proxies from cache")
        except Exception as e:
            logger.warning(f"ProxyManager: cache load failed: {e}")

    def _save_cache(self) -> None:
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "saved_at": time.time(),
                "entries": [e.to_dict() for e in self.entries.values() if e.source != "primary"],
            }
            CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"ProxyManager: cache save failed: {e}")

    # ------------------------------------------------------------------ #
    # Policy helper                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def strategy_for(portal: str) -> str:
        return PORTAL_STRATEGY.get(portal, "hybrid")
