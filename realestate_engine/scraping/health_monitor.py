"""Scraping health monitoring and metrics collection.

Tracks scraping performance, success rates, proxy health, and anti-bot detection events.
Provides visibility into scraping operations for production monitoring.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class ScrapingSession:
    """Record of a single scraping session."""
    portal: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    listings_count: int = 0
    error: Optional[str] = None
    proxy_used: Optional[str] = None
    blocked: bool = False
    blocker_type: Optional[str] = None

    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


@dataclass
class ProxyStats:
    """Statistics for a single proxy."""
    url: str
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    last_used: float = 0.0
    last_success: float = 0.0
    last_failure: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests


class ScrapingHealthMonitor:
    """Monitor scraping health and metrics."""

    def __init__(self):
        self.sessions: List[ScrapingSession] = []
        self.current_sessions: Dict[str, ScrapingSession] = {}
        self.proxy_stats: Dict[str, ProxyStats] = defaultdict(ProxyStats)
        self.portal_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_listings": 0,
            "total_duration": 0.0,
            "blocked_count": 0,
            "blocking_events": defaultdict(int)
        })
        self.anti_bot_events: List[Dict] = []

    def record_session_start(self, portal: str, proxy_url: Optional[str] = None):
        """Record start of scraping session."""
        session = ScrapingSession(
            portal=portal,
            start_time=time.time(),
            proxy_used=proxy_url
        )
        self.current_sessions[portal] = session
        self.portal_stats[portal]["total_sessions"] += 1
        logger.debug(f"[HealthMonitor] Session started for {portal}")

    def record_session_end(
        self,
        portal: str,
        success: bool,
        listings_count: int = 0,
        error: Optional[str] = None,
        blocked: bool = False,
        blocker_type: Optional[str] = None
    ):
        """Record end of scraping session."""
        if portal not in self.current_sessions:
            logger.warning(f"[HealthMonitor] No active session for {portal}")
            return

        session = self.current_sessions.pop(portal)
        session.end_time = time.time()
        session.success = success
        session.listings_count = listings_count
        session.error = error
        session.blocked = blocked
        session.blocker_type = blocker_type

        self.sessions.append(session)
        stats = self.portal_stats[portal]

        if success:
            stats["successful_sessions"] += 1
            stats["total_listings"] += listings_count
        else:
            stats["failed_sessions"] += 1

        stats["total_duration"] += session.duration

        if blocked and blocker_type:
            stats["blocked_count"] += 1
            stats["blocking_events"][blocker_type] += 1
            self.anti_bot_events.append({
                "portal": portal,
                "blocker_type": blocker_type,
                "timestamp": time.time()
            })

        logger.debug(
            f"[HealthMonitor] Session ended for {portal}: "
            f"success={success}, listings={listings_count}, duration={session.duration:.2f}s"
        )

    def record_proxy_use(self, proxy_url: str, success: bool, latency_ms: float = 0.0):
        """Record proxy usage."""
        stats = self.proxy_stats[proxy_url]
        stats.total_requests += 1
        stats.last_used = time.time()

        if success:
            stats.success_count += 1
            stats.last_success = time.time()
            if latency_ms > 0:
                # Update moving average
                if stats.avg_latency_ms == 0:
                    stats.avg_latency_ms = latency_ms
                else:
                    stats.avg_latency_ms = 0.7 * stats.avg_latency_ms + 0.3 * latency_ms
        else:
            stats.failure_count += 1
            stats.last_failure = time.time()

    def get_health_report(self) -> Dict:
        """Generate comprehensive health report."""
        portal_summaries = {}
        for portal, stats in self.portal_stats.items():
            total_sessions = stats["total_sessions"]
            if total_sessions == 0:
                continue

            portal_summaries[portal] = {
                "total_sessions": total_sessions,
                "successful_sessions": stats["successful_sessions"],
                "failed_sessions": stats["failed_sessions"],
                "success_rate": stats["successful_sessions"] / total_sessions,
                "total_listings": stats["total_listings"],
                "avg_listings_per_session": stats["total_listings"] / total_sessions if total_sessions > 0 else 0,
                "avg_duration": stats["total_duration"] / total_sessions if total_sessions > 0 else 0,
                "blocked_count": stats["blocked_count"],
                "blocking_events": dict(stats["blocking_events"])
            }

        # Calculate overall proxy health
        proxy_summaries = {}
        for url, stats in self.proxy_stats.items():
            proxy_summaries[url] = {
                "success_rate": stats.success_rate,
                "total_requests": stats.total_requests,
                "success_count": stats.success_count,
                "failure_count": stats.failure_count,
                "avg_latency_ms": stats.avg_latency_ms,
                "last_used": stats.last_used
            }

        # Recent anti-bot events (last hour)
        recent_anti_bot = [
            e for e in self.anti_bot_events
            if time.time() - e["timestamp"] < 3600
        ]

        return {
            "portals": portal_summaries,
            "proxies": proxy_summaries,
            "recent_anti_bot_events": len(recent_anti_bot),
            "total_anti_bot_events": len(self.anti_bot_events),
            "active_sessions": list(self.current_sessions.keys())
        }

    def get_portal_health(self, portal: str) -> Optional[Dict]:
        """Get health report for a specific portal."""
        if portal not in self.portal_stats:
            return None

        stats = self.portal_stats[portal]
        total_sessions = stats["total_sessions"]

        if total_sessions == 0:
            return {
                "portal": portal,
                "total_sessions": 0,
                "status": "no_data"
            }

        return {
            "portal": portal,
            "total_sessions": total_sessions,
            "successful_sessions": stats["successful_sessions"],
            "failed_sessions": stats["failed_sessions"],
            "success_rate": stats["successful_sessions"] / total_sessions,
            "total_listings": stats["total_listings"],
            "avg_listings_per_session": stats["total_listings"] / total_sessions,
            "avg_duration": stats["total_duration"] / total_sessions,
            "blocked_count": stats["blocked_count"],
            "blocking_events": dict(stats["blocking_events"]),
            "status": "healthy" if stats["successful_sessions"] / total_sessions > 0.8 else "degraded"
        }

    def get_proxy_health(self, proxy_url: Optional[str] = None) -> Dict:
        """Get health report for proxy or all proxies."""
        if proxy_url:
            if proxy_url not in self.proxy_stats:
                return {"proxy": proxy_url, "status": "no_data"}
            stats = self.proxy_stats[proxy_url]
            return {
                "proxy": proxy_url,
                "success_rate": stats.success_rate,
                "total_requests": stats.total_requests,
                "avg_latency_ms": stats.avg_latency_ms,
                "status": "healthy" if stats.success_rate > 0.7 else "degraded"
            }
        else:
            return {
                "total_proxies": len(self.proxy_stats),
                "healthy_proxies": sum(1 for s in self.proxy_stats.values() if s.success_rate > 0.7),
                "degraded_proxies": sum(1 for s in self.proxy_stats.values() if 0.3 < s.success_rate <= 0.7),
                "failed_proxies": sum(1 for s in self.proxy_stats.values() if s.success_rate <= 0.3)
            }

    def clear_old_sessions(self, max_age_hours: int = 24):
        """Clear old session data to prevent memory bloat."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        original_count = len(self.sessions)
        self.sessions = [s for s in self.sessions if s.start_time > cutoff_time]
        cleared = original_count - len(self.sessions)
        if cleared > 0:
            logger.info(f"[HealthMonitor] Cleared {cleared} old sessions")

    def reset_portal_stats(self, portal: str):
        """Reset statistics for a specific portal."""
        if portal in self.portal_stats:
            del self.portal_stats[portal]
        logger.info(f"[HealthMonitor] Reset stats for portal {portal}")
