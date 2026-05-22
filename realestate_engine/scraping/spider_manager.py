"""Spider Manager orchestrating scraping cycles.

Enhanced with:
- Circuit Breaker pattern to protect proxies and avoid bans
- Rate limiting per domain
- Parallel scraping capabilities (tier-based)
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.scraping.proxy_manager import ProxyManager
from realestate_engine.scraping.portal_rate_limiter import PortalRateLimiter
from realestate_engine.scraping.health_monitor import ScrapingHealthMonitor
from realestate_engine.scraping.spider_config import SpiderConfig
from realestate_engine.infrastructure.redis_client import get_redis
from realestate_engine.utils.job_logger import JobLogger


class CircuitBreaker:
    """Protects against continuous scraping failures (IP bans, layout changes)."""
    
    def __init__(self, failure_threshold: int = 3, cooldown_minutes: int = 30):
        self.failure_threshold = failure_threshold
        self.cooldown_minutes = cooldown_minutes
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False
        
    def record_success(self):
        self.failures = 0
        self.is_open = False
        self.last_failure_time = None
        
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit Breaker OPENED! Waiting {self.cooldown_minutes}m before next attempt.")
            
    def can_execute(self) -> bool:
        if not self.is_open:
            return True
            
        # Check if cooldown has expired
        if self.last_failure_time and datetime.now() > self.last_failure_time + timedelta(minutes=self.cooldown_minutes):
            logger.info("Circuit Breaker HALF-OPEN (Testing if system recovered).")
            return True
            
        return False


class SpiderManager:
    """Orchestrates all scraping tasks, managing rate limits and failures."""

    # Per-portal rate-limit budget (requests/min) — conservative defaults.
    DEFAULT_RATE_BUDGET: Dict[str, int] = {
        "idealista": 10, "imovirtual": 60, "casa_sapo": 20, "era": 20,
        "remax": 20, "supercasa": 20, "century21": 20, "olx": 15,
        "bpi": 30, "caixa": 30, "santander": 30, "millennium": 30,
    }

    def __init__(self):
        self.repo = DatabaseRepository()
        self.proxy_manager = ProxyManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.redis = get_redis()
        self.rate_limiter = PortalRateLimiter()
        self.health_monitor = ScrapingHealthMonitor()

    def _get_spider_class(self, spider_name: str):
        """Dynamically load spider class with registry fallback."""
        spiders = {}

        # Tier 1 - Nacionais (high priority)
        try:
            from realestate_engine.scraping.spiders.idealista_spider_nodriver import IdealistaSpider
            spiders["idealista"] = IdealistaSpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.imovirtual_nextdata_spider import ImovirtualNextDataSpider
            spiders["imovirtual"] = ImovirtualNextDataSpider
        except ImportError:
            try:
                from realestate_engine.scraping.spiders.imovirtual_spider_nodriver import ImovirtualSpider
                spiders["imovirtual"] = ImovirtualSpider
            except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider
            spiders["casa_sapo"] = CasaSapoDirectSpider
        except ImportError:
            try:
                from realestate_engine.scraping.spiders.casa_sapo_spider_nodriver import CasaSapoSpider
                spiders["casa_sapo"] = CasaSapoSpider
            except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.olx_spider_nodriver import OLXSpider
            spiders["olx"] = OLXSpider
        except ImportError: pass

        # Tier 2 - Bancários (bank-owned properties)
        try:
            from realestate_engine.scraping.spiders.bpi_spider_nodriver import BPISpider
            spiders["bpi"] = BPISpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.caixa_spider_nodriver import CaixaSpider
            spiders["caixa"] = CaixaSpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.santander_spider_nodriver import SantanderSpider
            spiders["santander"] = SantanderSpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.millennium_spider_nodriver import MillenniumSpider
            spiders["millennium"] = MillenniumSpider
        except ImportError: pass

        # Tier 3 - Regionais
        try:
            from realestate_engine.scraping.spiders.era_spider_nodriver import ERASpider
            spiders["era"] = ERASpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider
            spiders["remax"] = REMAXDirectSpider
        except ImportError:
            try:
                from realestate_engine.scraping.spiders.remax_spider_nodriver import REMAXSpider
                spiders["remax"] = REMAXSpider
            except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.supercasa_spider_nodriver import SuperCasaSpider
            spiders["supercasa"] = SuperCasaSpider
        except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.century21_spider_nodriver import Century21Spider
            spiders["century21"] = Century21Spider
        except ImportError: pass

        return spiders.get(spider_name)

    async def run_spider(self, spider_name: str, max_pages: int = 20, headless: bool = True) -> List[Dict]:
        """Run a single spider with circuit breaking."""
        if spider_name not in self.circuit_breakers:
            self.circuit_breakers[spider_name] = CircuitBreaker()
            
        cb = self.circuit_breakers[spider_name]
        
        if not cb.can_execute():
            logger.warning(f"Skipping {spider_name} due to open Circuit Breaker.")
            return []

        # Portal-specific adaptive rate limiting
        if not await self.rate_limiter.wait_if_needed(spider_name):
            logger.warning(f"Portal {spider_name} is rate limited (banned); skipping this cycle")
            self.health_monitor.record_session_end(
                spider_name,
                success=False,
                error="Rate limited (banned)"
            )
            return []

        # Redis-backed per-portal rate limit. If Redis is unavailable we fall
        # open (see RedisCache.allow_request), but we still log the decision.
        budget = self.DEFAULT_RATE_BUDGET.get(spider_name, 20)
        if not self.redis.allow_request(f"scraping:{spider_name}", budget):
            logger.warning(f"Rate limit hit for {spider_name}; skipping this cycle")
            self.health_monitor.record_session_end(
                spider_name,
                success=False,
                error="Redis rate limit hit"
            )
            return []

        spider_cls = self._get_spider_class(spider_name)
        if not spider_cls:
            logger.error(f"Spider not found: {spider_name}")
            return []

        logger.info(f"Starting spider: {spider_name} (Max pages: {max_pages})")
        
        # Check if spider accepts health_monitor parameter
        import inspect
        sig = inspect.signature(spider_cls.__init__)
        if 'health_monitor' in sig.parameters:
            spider = spider_cls(proxy_manager=self.proxy_manager, health_monitor=self.health_monitor)
        else:
            spider = spider_cls(proxy_manager=self.proxy_manager)

        async with JobLogger(f"scraping.{spider_name}") as jl:
            try:
                # Enforce max timeout to avoid hanging processes.
                # 1800s (30 min) accommodates 8 regions × 20 pages at ~2.5s/page.
                results = await asyncio.wait_for(
                    spider.run(max_pages=max_pages, headless=headless),
                    timeout=1800.0,
                )
                cb.record_success()

                # Save raw results
                if results:
                    from realestate_engine.database.models import RawListing
                    raw_models = []
                    for r in results:
                        existing_raw = self.repo.get_raw_listing_by_source(r["source_portal"], r["source_id"])
                        if existing_raw and existing_raw.raw_data == r["raw_data"]:
                            continue
                        raw_models.append(RawListing(
                            source_portal=r["source_portal"],
                            source_id=r["source_id"],
                            source_url=r["source_url"],
                            scrape_timestamp=r["scrape_timestamp"],
                            raw_data=r["raw_data"],
                        ))
                    if raw_models:
                        self.repo.create_raw_listings_batch(raw_models)

                jl.records_processed = len(results)
                self.health_monitor.record_session_end(
                    spider_name,
                    success=True,
                    listings_count=len(results)
                )
                self.rate_limiter.record_success(spider_name)
                return results
            except asyncio.TimeoutError:
                logger.error(f"Spider {spider_name} timed out after 600s.")
                cb.record_failure()
                self.health_monitor.record_session_end(
                    spider_name,
                    success=False,
                    error="Timeout"
                )
                self.rate_limiter.record_failure(spider_name)
                return []
            except Exception as e:
                logger.error(f"Spider {spider_name} failed: {e}")
                cb.record_failure()
                self.health_monitor.record_session_end(
                    spider_name,
                    success=False,
                    error=str(e)
                )
                self.rate_limiter.record_failure(spider_name)
                raise

    DEFAULT_CYCLE_PORTALS = [
        # Tier 1 - Nacionais
        "idealista", "imovirtual", "casa_sapo", "olx",
        # Tier 2 - Bancários
        "bpi", "caixa", "santander", "millennium",
        # Tier 3 - Regionais
        "era", "remax", "supercasa", "century21",
    ]

    async def run_all_cycle(
        self,
        active_portals: List[str] = None,
        config: Optional[SpiderConfig] = None,
    ) -> Dict[str, int]:
        """Run a full scraping cycle for active portals.

        Isolates per-portal failures so a crash in one spider never halts the
        whole cycle. All runs (success or fail) are persisted via JobLogger.
        Portal runs are parallelized with a semaphore to limit concurrency.
        """
        portals = active_portals or list(self.DEFAULT_CYCLE_PORTALS)
        config = config or SpiderConfig()

        # Tier-based concurrency: more slots for lighter portals
        tier1 = [p for p in portals if p in ("idealista", "imovirtual", "casa_sapo", "olx")]
        tier2 = [p for p in portals if p in ("bpi", "caixa", "santander", "millennium")]
        tier3 = [p for p in portals if p not in tier1 and p not in tier2]

        logger.info(f"Starting full scraping cycle: Tier1={len(tier1)}, Tier2={len(tier2)}, Tier3={len(tier3)}")

        semaphore = asyncio.Semaphore(4)  # increased from 3 for better throughput

        async def _scrape_one(portal: str) -> tuple[str, int]:
            await asyncio.sleep(2)  # natural delay before starting
            async with semaphore:
                try:
                    results = await self.run_spider(portal, max_pages=config.max_pages, headless=config.headless)
                    return portal, len(results)
                except Exception as e:
                    logger.error(f"Spider {portal} raised unrecoverable error: {e}")
                    return portal, 0

        results = await asyncio.gather(*[_scrape_one(p) for p in portals])
        summary: Dict[str, int] = dict(results)

        logger.info(f"Scraping cycle complete. Summary: {summary}")
        return summary

    async def run_all_cycle_verbose(
        self,
        active_portals: Optional[List[str]] = None,
        config: Optional[SpiderConfig] = None,
    ) -> tuple[Dict[str, int], Dict[str, Exception]]:
        """Verbose variant of ``run_all_cycle`` that surfaces per-portal errors.

        Returns ``(summary, errors)`` where ``summary`` mirrors the original
        ``run_all_cycle`` shape (portal → record count) and ``errors`` maps
        any portal that raised to its exception. UI layers can use this to
        show which portal failed and why instead of receiving silent zeros.
        """
        portals = active_portals or list(self.DEFAULT_CYCLE_PORTALS)
        config = config or SpiderConfig()
        logger.info(f"[verbose] Starting full scraping cycle for {len(portals)} portals (max 3 concurrent).")

        semaphore = asyncio.Semaphore(3)

        async def _scrape_one(portal: str) -> tuple[str, int, Optional[Exception]]:
            await asyncio.sleep(2)
            async with semaphore:
                try:
                    results = await self.run_spider(portal, max_pages=config.max_pages, headless=config.headless)
                    return portal, len(results), None
                except Exception as e:  # noqa: BLE001 — captured for UI surfacing
                    logger.error(f"Spider {portal} raised: {e}")
                    return portal, 0, e

        results = await asyncio.gather(*[_scrape_one(p) for p in portals])
        summary: Dict[str, int] = {p: count for p, count, _ in results}
        errors: Dict[str, Exception] = {p: exc for p, _, exc in results if exc is not None}

        logger.info(f"[verbose] Cycle complete. Summary: {summary} | Errors: {list(errors)}")
        return summary, errors

    async def run_all_spiders(
        self,
        active_portals: Optional[List[str]] = None,
        config: Optional[SpiderConfig] = None,
    ) -> List[Dict]:
        """Run all active spiders and return the flattened listing payloads.

        This method keeps backward compatibility with older scheduler jobs that
        expect a list of listing dictionaries rather than a per-portal summary.
        """
        portals = active_portals or list(self.DEFAULT_CYCLE_PORTALS)
        config = config or SpiderConfig()
        logger.info(f"Starting flattened scraping run for {len(portals)} portals (max 3 concurrent).")

        semaphore = asyncio.Semaphore(3)

        async def _scrape_one(portal: str) -> List[Dict]:
            await asyncio.sleep(2)
            async with semaphore:
                try:
                    return await self.run_spider(portal, max_pages=config.max_pages, headless=config.headless)
                except Exception as e:
                    logger.error(f"Spider {portal} raised unrecoverable error: {e}")
                    return []

        results = await asyncio.gather(*[_scrape_one(p) for p in portals])
        flattened: List[Dict] = [listing for portal_results in results for listing in portal_results]

        logger.info(f"Flattened scraping run complete. Total listings: {len(flattened)}")
        return flattened
