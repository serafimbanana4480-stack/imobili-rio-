"""Per-portal rate limiting with adaptive backoff for scraping.

Implements portal-specific rate limits based on observed aggressiveness:
- Casa Sapo: VERY HIGH (10-20s delay)
- Idealista: HIGH (5-10s delay)
- Imovirtual: LOW (1-3s delay)
- REMAX: MEDIUM (3-5s delay)
- ERA: MEDIUM (3-5s delay)
- Supercasa: MEDIUM (3-5s delay)
- Century21: LOW (2-4s delay)
- OLX: HIGH (5-8s delay)
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger


@dataclass
class PortalConfig:
    """Configuration for a specific portal's rate limiting."""
    name: str
    base_delay: float  # Base delay in seconds
    max_delay: float  # Maximum delay in seconds
    jitter: float  # Jitter factor (0-1)
    requests_per_minute: int  # Max requests per minute
    ban_threshold: int  # Failures before considering banned
    recovery_time: int  # Seconds to wait after ban


# Portal configurations based on observed aggressiveness
PORTAL_CONFIGS: Dict[str, PortalConfig] = {
    "imovirtual": PortalConfig(
        name="imovirtual",
        base_delay=1.5,
        max_delay=5.0,
        jitter=0.5,
        requests_per_minute=40,
        ban_threshold=10,
        recovery_time=300
    ),
    "casa_sapo": PortalConfig(
        name="casa_sapo",
        base_delay=15.0,  # Very conservative
        max_delay=30.0,
        jitter=0.3,
        requests_per_minute=4,
        ban_threshold=5,
        recovery_time=1800  # 30 minutes
    ),
    "idealista": PortalConfig(
        name="idealista",
        base_delay=7.0,
        max_delay=15.0,
        jitter=0.4,
        requests_per_minute=8,
        ban_threshold=7,
        recovery_time=900  # 15 minutes
    ),
    "remax": PortalConfig(
        name="remax",
        base_delay=3.0,
        max_delay=5.0,
        jitter=0.3,
        requests_per_minute=20,
        ban_threshold=8,
        recovery_time=600  # 10 minutes
    ),
    "era": PortalConfig(
        name="era",
        base_delay=3.0,
        max_delay=5.0,
        jitter=0.3,
        requests_per_minute=20,
        ban_threshold=8,
        recovery_time=600  # 10 minutes
    ),
    "supercasa": PortalConfig(
        name="supercasa",
        base_delay=3.0,
        max_delay=5.0,
        jitter=0.3,
        requests_per_minute=20,
        ban_threshold=8,
        recovery_time=600  # 10 minutes
    ),
    "century21": PortalConfig(
        name="century21",
        base_delay=2.0,
        max_delay=4.0,
        jitter=0.4,
        requests_per_minute=30,
        ban_threshold=12,
        recovery_time=300  # 5 minutes
    ),
    "olx": PortalConfig(
        name="olx",
        base_delay=5.0,
        max_delay=8.0,
        jitter=0.4,
        requests_per_minute=12,
        ban_threshold=7,
        recovery_time=900  # 15 minutes
    ),
}


class PortalRateLimiter:
    """Per-portal rate limiting with adaptive backoff."""

    def __init__(self):
        self.request_counts: Dict[str, int] = {}
        self.last_request_times: Dict[str, float] = {}
        self.failure_counts: Dict[str, int] = {}
        self.ban_until: Dict[str, float] = {}

    async def wait_if_needed(self, portal: str) -> bool:
        """Wait if rate limit reached. Returns False if banned."""
        config = PORTAL_CONFIGS.get(portal)
        if not config:
            logger.warning(f"No config for portal {portal}, using default")
            config = PortalConfig(
                name=portal,
                base_delay=2.0,
                max_delay=10.0,
                jitter=0.5,
                requests_per_minute=20,
                ban_threshold=10,
                recovery_time=600
            )

        # Check if banned
        if portal in self.ban_until:
            if time.time() < self.ban_until[portal]:
                logger.warning(f"Portal {portal} is banned until {self.ban_until[portal]}")
                return False
            else:
                # Ban expired
                del self.ban_until[portal]
                self.failure_counts[portal] = 0
                logger.info(f"Portal {portal} ban expired, resuming")

        # Calculate delay
        base_delay = config.base_delay
        if portal in self.failure_counts:
            # Exponential backoff based on failures
            backoff_factor = min(2 ** self.failure_counts[portal], 4)
            base_delay = min(base_delay * backoff_factor, config.max_delay)

        # Add jitter
        delay = base_delay * (1 - config.jitter + random.random() * 2 * config.jitter)

        # Enforce requests per minute
        if portal in self.last_request_times:
            time_since_last = time.time() - self.last_request_times[portal]
            min_interval = 60 / config.requests_per_minute
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                logger.debug(f"Rate limiting {portal}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        await asyncio.sleep(delay)
        self.last_request_times[portal] = time.time()
        self.request_counts[portal] = self.request_counts.get(portal, 0) + 1

        return True

    def record_failure(self, portal: str):
        """Record a failure for the portal."""
        self.failure_counts[portal] = self.failure_counts.get(portal, 0) + 1
        config = PORTAL_CONFIGS.get(portal)

        if config and self.failure_counts[portal] >= config.ban_threshold:
            self.ban_until[portal] = time.time() + config.recovery_time
            logger.error(
                f"Portal {portal} banned for {config.recovery_time}s "
                f"due to {self.failure_counts[portal]} failures"
            )

    def record_success(self, portal: str):
        """Record a success for the portal."""
        self.failure_counts[portal] = 0

    def get_stats(self, portal: Optional[str] = None) -> Dict:
        """Get rate limiting statistics."""
        if portal:
            return {
                "portal": portal,
                "request_count": self.request_counts.get(portal, 0),
                "failure_count": self.failure_counts.get(portal, 0),
                "is_banned": portal in self.ban_until and time.time() < self.ban_until[portal],
                "ban_until": self.ban_until.get(portal, 0),
                "config": PORTAL_CONFIGS.get(portal).__dict__ if portal in PORTAL_CONFIGS else None
            }
        else:
            return {
                "portals": {
                    p: self.get_stats(p)
                    for p in PORTAL_CONFIGS.keys()
                }
            }

    def reset_portal(self, portal: str):
        """Reset rate limiting for a specific portal."""
        if portal in self.request_counts:
            del self.request_counts[portal]
        if portal in self.last_request_times:
            del self.last_request_times[portal]
        if portal in self.failure_counts:
            del self.failure_counts[portal]
        if portal in self.ban_until:
            del self.ban_until[portal]
        logger.info(f"Reset rate limiting for portal {portal}")
