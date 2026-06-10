"""Base spider using Nodriver for anti-bot evasion.

Enhanced with:
- Timeout protection for all operations
- Comprehensive debug logging with HTML snapshots
- Multiple selector fallback strategies
- Retry logic with exponential backoff
- Improved stealth features
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from loguru import logger

import nodriver as uc

from realestate_engine.scraping.browser_resolver import (
    BrowserNotFoundError,
    require_browser,
)
from realestate_engine.scraping.proxy_manager import ProxyManager
from realestate_engine.scraping.stealth_manager import StealthManager
from realestate_engine.scraping.session_manager import SessionManager
from realestate_engine.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()



class BaseSpiderNodriver(ABC):
    """Professional-grade Nodriver spider with full stealth and resilience."""
    
    name: str = "base"
    base_url: str = ""
    sleep_range = (4, 10)
    max_pages = 5
    selector_fallbacks: List[str] = []
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.stealth = StealthManager()
        self.session_manager = SessionManager()
        self.results: List[Dict] = []
        self.browser = None
        self.tab = None
        self.stats = {"scraped": 0, "errors": 0, "pages": 0, "retries": 0}
        self.max_retries = 3
        self.retry_delay = 5
        self.is_blocked = False

    async def start_browser(self, headless: bool = True):
        """Start browser with professional args and proxy.

        Auto-resolves a local Chrome/Chromium binary (Windows/macOS/Linux) and
        respects ``REE_CHROME_PATH`` if set. Raises ``BrowserNotFoundError``
        with install instructions when nothing is available.
        """
        proxy = self.proxy_manager.get_proxy()
        args = self.stealth.get_browser_args()
        if proxy:
            args.append(f"--proxy-server={proxy}")

        try:
            browser_path = require_browser()
        except BrowserNotFoundError as exc:
            logger.error(f"[{self.name}] {exc}")
            raise

        logger.info(f"[{self.name}] Using browser: {browser_path}")
        self.browser = await uc.start(
            browser_executable_path=browser_path,
            browser_args=args,
            headless=headless,
        )
        self.tab = await self.browser.get("about:blank")
        logger.info(f"[{self.name}] Professional browser started (headless={headless})")


    async def scroll_page(self, scroll_count: int = 3):
        """Scroll down the page multiple times with human-like pauses.

        Used by child spiders to load lazy content before parsing.
        """
        for _ in range(scroll_count):
            try:
                await self.tab.evaluate("window.scrollBy({top: 800, behavior: 'smooth'})")
                await asyncio.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                logger.warning(f"[{self.name}] Scroll interrupted: {e}")
                break

    async def human_like_behavior(self):
        """Simulate complex human reading/browsing patterns."""
        # Variable scroll patterns
        scroll_pattern = [
            (random.randint(300, 800), random.uniform(1.0, 3.0)),
            (random.randint(-200, -50), random.uniform(0.5, 1.5)),  # Scroll up
            (random.randint(400, 900), random.uniform(2.0, 4.0)),
        ]
        
        for amount, pause in scroll_pattern:
            try:
                await self.tab.evaluate(f"window.scrollBy({{top: {amount}, behavior: 'smooth'}})")
                await asyncio.sleep(pause)
                
                # Random mouse "jiggle" or hover simulation could be added here
                
                if random.random() > 0.8:
                    await asyncio.sleep(random.uniform(3, 6))
            except Exception as e:
                logger.warning(f"[{self.name}] Behavioral simulation interrupted: {e}")
                break

    async def detect_blocking(self) -> bool:
        """Check for anti-bot markers in the current page."""
        try:
            content = await self.tab.get_content()
            markers = ["cf-challenge", "datadome", "captcha", "Access Denied", "403 Forbidden", "captcha-delivery"]
            for marker in markers:
                if marker.lower() in content.lower():
                    logger.error(f"[{self.name}] Anti-bot detected! (Marker: {marker})")
                    self.is_blocked = True
                    return True
        except:
            pass
        return False
    
    async def handle_captcha(self) -> bool:
        """Try to handle captcha by waiting and retrying."""
        logger.warning(f"[{self.name}] Captcha detected, waiting 30 seconds...")
        await asyncio.sleep(30)
        # Check if captcha is still there
        if await self.detect_blocking():
            logger.error(f"[{self.name}] Captcha still present after wait")
            return False
        logger.info(f"[{self.name}] Captcha resolved")
        return True

    async def safe_evaluate(self, script: str, timeout: float = 10.0) -> any:
        """Evaluate JavaScript with timeout protection."""
        try:
            result = await asyncio.wait_for(self.tab.evaluate(script), timeout=timeout)
            # Handle ExceptionDetails objects from nodriver
            if hasattr(result, 'exceptionDetails'):
                logger.error(f"[{self.name}] Script evaluation returned exception: {result.exceptionDetails}")
                return None
            return result
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] Script evaluation timeout after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"[{self.name}] Script evaluation error: {e}")
            return None
            
    async def take_debug_snapshot(self):
        """Take a snapshot of current page HTML for debugging."""
        try:
            html = await self.tab.evaluate("document.documentElement.outerHTML")
            logger.debug(f"[{self.name}] Page HTML snapshot (first 1000 chars): {html[:1000]}")
            return html
        except Exception as e:
            logger.warning(f"[{self.name}] Could not take HTML snapshot: {e}")
            return None

    async def wait_for_selector(self, selector: str, timeout: float = 20.0, poll: float = 0.5) -> int:
        """Poll the DOM until at least one element matches ``selector``.

        Returns the match count (0 on timeout). Essential for SPA portals
        that render property cards after client-side hydration.
        """
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            count = await self.safe_evaluate(
                f"document.querySelectorAll({selector!r}).length", timeout=5.0
            )
            try:
                count = int(count or 0)
            except (TypeError, ValueError):
                count = 0
            if count > 0:
                return count
            await asyncio.sleep(poll)
        return 0

    @abstractmethod
    async def parse_page(self, page_num: int) -> List[Dict]:
        """Parse a single search result page."""
        pass
    
    @abstractmethod
    async def get_next_page(self) -> bool:
        """Navigate to next page. Return False if no more pages."""
        pass

    async def retry_operation(self, operation, *args, **kwargs):
        """Retry operation with captcha handling and proxy rotation on block."""
        for attempt in range(self.max_retries):
            try:
                if self.is_blocked:
                    # Try to handle captcha first
                    if await self.handle_captcha():
                        self.is_blocked = False
                        return await operation(*args, **kwargs)
                    
                    # If captcha failed, rotate proxy
                    logger.info(f"[{self.name}] Rotating proxy due to block...")
                    await self.close_browser()
                    await self.start_browser()
                    await self.tab.get(self.base_url)
                    await self.session_manager.restore_session(self.tab, self.name)
                    self.is_blocked = False
                
                return await operation(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[{self.name}] Attempt {attempt+1} failed: {e}")
                if await self.detect_blocking():
                    continue
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        raise Exception(f"Operation failed after {self.max_retries} attempts")

    async def _dummy_operation(self):
        pass

    async def run(self, max_pages: Optional[int] = None, headless: bool = True) -> List[Dict]:
        """Full resilient professional lifecycle."""
        target_pages = max_pages or self.max_pages
        try:
            await self.start_browser(headless=headless)
            
            await self.tab.get(self.base_url)
            await self.session_manager.restore_session(self.tab, self.name)
            await self.stealth.apply_stealth(self.tab)
            
            for p in range(1, target_pages + 1):
                if await self.detect_blocking():
                    # Trigger retry logic which handles rotation
                    await self.retry_operation(self._dummy_operation) 
                
                logger.info(f"[{self.name}] Scraping page {p}")
                # Retry parsing up to 3 times on failure
                listings = []
                for attempt in range(1, self.max_retries + 1):
                    try:
                        listings = await self.parse_page(p)
                        break
                    except Exception as e:
                        logger.warning(f"[{self.name}] parse_page attempt {attempt} failed: {e}")
                        if attempt >= self.max_retries:
                            raise
                        await asyncio.sleep(self.retry_delay * attempt)
                self.results.extend(listings)
                self.stats["pages"] += 1
                self.stats["scraped"] += len(listings)
                
                if p < target_pages:
                    await self.human_like_behavior()
                    has_next = await self.get_next_page()
                    if not has_next: break
                    # Aumentar delay para evitar bloqueio (Casa Sapo é agressivo)
                    await self.smart_sleep(10, 20)
            
            await self.session_manager.save_session(self.tab, self.name)
            metrics.record_listings_scraped(self.name, len(self.results))
            return self.results
        except Exception as e:
            logger.error(f"[{self.name}] Professional life cycle failed: {e}")
            raise
        finally:
            await self.close_browser()
            
    async def smart_sleep(self, min_sec: Optional[float] = None, max_sec: Optional[float] = None):
        mn = min_sec or self.sleep_range[0]
        mx = max_sec or self.sleep_range[1]
        duration = random.weibullvariate((mx + mn) / 2, 2)
        duration = max(mn, min(mx, duration))
        await asyncio.sleep(duration)
    
    async def close_browser(self):
        if self.browser:
            try:
                self.browser.stop()
            except:
                pass
            logger.info(f"[{self.name}] Browser closed")

    def to_raw_listing(self, data: Dict) -> Dict:
        import uuid
        from datetime import datetime, UTC
        source_id = data.get("source_id", "")
        if not source_id or source_id.strip() == "":
            source_id = str(uuid.uuid4())[:8]
        return {
            "id": str(uuid.uuid4()),
            "source_portal": self.name,
            "source_id": source_id,
            "source_url": data.get("url", ""),
            "scrape_timestamp": datetime.now(UTC).isoformat(),
            "raw_data": data,
        }

