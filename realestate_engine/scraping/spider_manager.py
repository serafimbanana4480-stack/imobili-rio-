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
    }

    def __init__(self):
        self.repo = DatabaseRepository()
        self.proxy_manager = ProxyManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.redis = get_redis()

    def _get_spider_class(self, spider_name: str):
        """Dynamically load spider class."""
        spiders = {}
        try:
            from realestate_engine.scraping.spiders.idealista_spider_nodriver import IdealistaSpider
            spiders["idealista"] = IdealistaSpider
        except ImportError: pass

        try:
            # Direct-fetch spider (Next.js __NEXT_DATA__) — no proxy, no browser
            from realestate_engine.scraping.spiders.imovirtual_nextdata_spider import ImovirtualNextDataSpider
            spiders["imovirtual"] = ImovirtualNextDataSpider
        except ImportError:
            try:
                from realestate_engine.scraping.spiders.imovirtual_spider_nodriver import ImovirtualSpider
                spiders["imovirtual"] = ImovirtualSpider
            except ImportError:
                pass

        try:
            # Direct-fetch via embedded JSON-LD Offers — no browser required.
            from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider
            spiders["casa_sapo"] = CasaSapoDirectSpider
        except ImportError:
            try:
                from realestate_engine.scraping.spiders.casa_sapo_spider_nodriver import CasaSapoSpider
                spiders["casa_sapo"] = CasaSapoSpider
            except ImportError: pass

        try:
            from realestate_engine.scraping.spiders.era_spider_nodriver import ERASpider
            spiders["era"] = ERASpider
        except ImportError: pass

        try:
            # Direct-fetch via sitemap + per-listing JSON-LD Product — no browser.
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

        try:
            from realestate_engine.scraping.spiders.olx_spider_nodriver import OLXSpider
            spiders["olx"] = OLXSpider
        except ImportError: pass

        return spiders.get(spider_name)

    async def run_spider(self, spider_name: str, max_pages: int = 20, headless: bool = True, region: Optional[str] = None) -> List[Dict]:
        """Run a single spider with circuit breaking."""
        if spider_name not in self.circuit_breakers:
            self.circuit_breakers[spider_name] = CircuitBreaker()
            
        cb = self.circuit_breakers[spider_name]
        
        if not cb.can_execute():
            logger.warning(f"Skipping {spider_name} due to open Circuit Breaker.")
            return []

        # Redis-backed per-portal rate limit. If Redis is unavailable we fall
        # open (see RedisCache.allow_request), but we still log the decision.
        budget = self.DEFAULT_RATE_BUDGET.get(spider_name, 20)
        if not self.redis.allow_request(f"scraping:{spider_name}", budget):
            logger.warning(f"Rate limit hit for {spider_name}; skipping this cycle")
            return []

        spider_cls = self._get_spider_class(spider_name)
        if not spider_cls:
            logger.error(f"Spider not found: {spider_name}")
            return []

        logger.info(f"Starting spider: {spider_name} (Max pages: {max_pages}, region: {region or 'default'})")
        # Pass region if the spider constructor accepts it
        try:
            spider = spider_cls(proxy_manager=self.proxy_manager, region=region)
        except TypeError:
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
                    from realestate_engine.etl.deduplicator import Deduplicator
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
                        # Cross-portal deduplication: mark duplicates in the batch
                        try:
                            existing_fps = self.repo.get_all_fingerprints()
                            deduped = Deduplicator.filter_duplicates(raw_models, existing_fps)
                            logger.info(f"Deduplication: {len(raw_models)} raw → {len(deduped)} unique fingerprints")
                        except Exception as e:
                            logger.warning(f"Deduplication step failed: {e}")

                jl.records_processed = len(results)
                return results
            except asyncio.TimeoutError:
                logger.error(f"Spider {spider_name} timed out after 1800s.")
                cb.record_failure()
                return []
            except Exception as e:
                logger.error(f"Spider {spider_name} failed: {e}")
                cb.record_failure()
                raise

    DEFAULT_CYCLE_PORTALS = [
        "idealista", "imovirtual", "casa_sapo", "era",
        "remax", "supercasa", "century21", "olx",
    ]

    async def run_all_cycle(self, active_portals: List[str] = None, regions: Optional[List[str]] = None) -> Dict[str, int]:
        """Run a full scraping cycle for active portals.

        Isolates per-portal failures so a crash in one spider never halts the
        whole cycle. All runs (success or fail) are persisted via JobLogger.
        """
        portals = active_portals or list(self.DEFAULT_CYCLE_PORTALS)
        logger.info(f"Starting full scraping cycle for {len(portals)} portals.")

        summary: Dict[str, int] = {}
        for portal in portals:
            # Adding a natural delay between firing different portals to avoid network congestion
            await asyncio.sleep(2)
            try:
                # If regions list provided, run spider for each region; else default region
                if regions:
                    total = 0
                    for region in regions:
                        results = await self.run_spider(portal, region=region)
                        total += len(results)
                    summary[portal] = total
                else:
                    results = await self.run_spider(portal)
                    summary[portal] = len(results)
            except Exception as e:
                logger.error(f"Spider {portal} raised unrecoverable error: {e}")
                summary[portal] = 0

        logger.info(f"Scraping cycle complete. Summary: {summary}")
        return summary

    async def run_all_cycle_verbose(
        self, active_portals: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
    ) -> tuple[Dict[str, int], Dict[str, Exception]]:
        """Verbose variant of ``run_all_cycle`` that surfaces per-portal errors.

        Returns ``(summary, errors)`` where ``summary`` mirrors the original
        ``run_all_cycle`` shape (portal → record count) and ``errors`` maps
        any portal that raised to its exception. UI layers can use this to
        show which portal failed and why instead of receiving silent zeros.
        """
        portals = active_portals or list(self.DEFAULT_CYCLE_PORTALS)
        logger.info(f"[verbose] Starting full scraping cycle for {len(portals)} portals.")

        summary: Dict[str, int] = {}
        errors: Dict[str, Exception] = {}
        for portal in portals:
            await asyncio.sleep(2)
            try:
                if regions:
                    total = 0
                    for region in regions:
                        results = await self.run_spider(portal, region=region)
                        total += len(results)
                    summary[portal] = total
                else:
                    results = await self.run_spider(portal)
                    summary[portal] = len(results)
            except Exception as e:  # noqa: BLE001 — captured for UI surfacing
                logger.error(f"Spider {portal} raised: {e}")
                summary[portal] = 0
                errors[portal] = e

        logger.info(f"[verbose] Cycle complete. Summary: {summary} | Errors: {list(errors)}")
        return summary, errors
