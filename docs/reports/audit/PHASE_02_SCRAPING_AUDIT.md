# PHASE 2: SCRAPING AUDIT
## Robustness, Anti-Bot, Proxies, Retry Strategies

**Date:** 2026-05-04  
**Auditor:** Principal Software Architect + Staff Engineer + SRE  
**Scope:** Complete scraping layer analysis for production scalability  
**Production Context:** System intended for commercial sale with 24/7 operation across 8 Portuguese real estate portals

---

## EXECUTIVE SUMMARY

**Overall Scraping Score:** 72/100

**Critical Issues:** 2  
**High Priority Issues:** 4  
**Medium Priority Issues:** 6  
**Low Priority Issues:** 3

**Key Findings:**
- Scraping architecture is sophisticated with dual approach (Nodriver + direct fetch)
- BaseSpiderNodriver implements professional anti-bot measures
- ImovirtualNextDataSpider demonstrates excellent direct-fetch optimization
- **CRITICAL:** No proxy rotation in production - IP exposure risk
- **CRITICAL:** No proxy pool management or health checking
- Anti-bot detection is basic (marker-based) without reputation tracking
- Retry logic is present but lacks circuit breaker pattern
- Session management exists but no distributed session persistence
- No scraping rate limiting per portal (can trigger bans)
- No scraping health monitoring or alerting

---

## 1. SPIDER ARCHITECTURE ANALYSIS

### 1.1 Current Architecture

**Status:** 🟢 GOOD DUAL APPROACH

**Architecture Pattern:**
```
SpiderManager
├── Direct Fetch Spiders (Fast, No Browser)
│   ├── ImovirtualNextDataSpider (8 regions)
│   ├── CasaSapoDirectSpider
│   └── REMAXDirectSpider
└── Nodriver Spiders (Browser-based, Anti-bot)
    ├── BaseSpiderNodriver (Base class)
    ├── IdealistaSpider
    ├── ERASpider
    ├── SupercasaSpider
    ├── Century21Spider
    └── OLXSpider
```

**Assessment:**
- **Positive:** Dual approach optimizes for both speed and coverage
- **Positive:** Direct spiders are 10-100x faster (no browser overhead)
- **Positive:** Base class provides consistent anti-bot measures
- **Positive:** Session management preserves cookies/state
- **Negative:** No unified interface between direct and Nodriver spiders
- **Negative:** No spider health monitoring
- **Negative:** No automatic fallback between spider types

### 1.2 Direct Fetch Spiders Analysis

**LOCATION:** `realestate_engine/scraping/spiders/imovirtual_nextdata_spider.py` (389 lines)

**Implementation Quality:** 🟢 EXCELLENT

**Code Analysis:**
```python
class ImovirtualNextDataSpider:
    """Direct-fetch Imovirtual spider (no browser, no proxy needed)."""
    
    name = "imovirtual"
    SEARCH_URLS = [
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/porto",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/lisboa",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/braga",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/coimbra",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/faro",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/setubal",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/aveiro",
        "https://www.imovirtual.com/pt/resultados/comprar/apartamento/leiria",
    ]
    max_pages = 20
    request_delay = (1.2, 2.8)  # Jitter seconds between pages
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        # ... realistic headers
    }
```

**Strengths:**
1. **Multi-region scraping:** 8 cities maximize coverage
2. **Cross-region deduplication:** `seen_ids` set prevents duplicates
3. **Defensive parsing:** `_walk_search_ads()` handles path changes
4. **Rate limiting:** Random delay (1.2-2.8s) with jitter
5. **Connection pooling:** `httpx.Limits(max_connections=4)`
6. **Error handling:** Comprehensive try/except for all failure modes
7. **Pagination detection:** Respects `totalPages` from API response
8. **Field extraction:** Comprehensive field mapping (location, price, area, features)

**Production-Ready Features:**
- ✅ Realistic User-Agent
- ✅ Proper Accept headers
- ✅ Connection pooling
- ✅ Rate limiting with jitter
- ✅ Timeout configuration (30s connect, 15s read)
- ✅ HTTP/2 disabled (more compatible)
- ✅ Follow redirects enabled
- ✅ Cross-region deduplication

**Limitations:**
- ⚠️ No proxy support (commented as optional but not used)
- ⚠️ No user-agent rotation
- ⚠️ No request signature randomization
- ⚠️ No request header randomization
- ⚠️ Hardcoded delay (should be adaptive based on response)

**Refactor Suggestion - Adaptive Rate Limiting:**
```python
class AdaptiveRateLimiter:
    """Adaptive rate limiting based on response headers and status codes."""
    
    def __init__(self, initial_delay: float = 1.0, max_delay: float = 10.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.current_delay = initial_delay
        self.success_count = 0
        self.failure_count = 0
    
    def get_delay(self, response_status: int, response_headers: Dict) -> float:
        """Calculate delay based on response."""
        # Check for rate limit headers
        if 'Retry-After' in response_headers:
            return float(response_headers['Retry-After'])
        
        # Back off on 429 (Too Many Requests)
        if response_status == 429:
            self.current_delay = min(self.current_delay * 2, self.max_delay)
            self.failure_count += 1
            return self.current_delay
        
        # Reduce delay on success
        if 200 <= response_status < 300:
            self.success_count += 1
            if self.success_count > 5:
                self.current_delay = max(self.current_delay * 0.9, self.initial_delay)
        
        # Add jitter
        import random
        return self.current_delay * (0.8 + random.random() * 0.4)

# Usage
rate_limiter = AdaptiveRateLimiter(initial_delay=1.2, max_delay=10.0)
resp = await client.get(url)
delay = rate_limiter.get_delay(resp.status_code, dict(resp.headers))
await asyncio.sleep(delay)
```

**Implementation Effort:** 1 day  
**Priority:** MEDIUM  
**Risk:** LOW

---

### 1.3 Nodriver Spiders Analysis

**LOCATION:** `realestate_engine/scraping/spiders/base_spider_nodriver.py` (292 lines)

**Implementation Quality:** 🟢 VERY GOOD

**Code Analysis:**
```python
class BaseSpiderNodriver(ABC):
    """Professional-grade Nodriver spider with full stealth and resilience."""
    
    sleep_range = (4, 10)
    max_pages = 5
    selector_fallbacks: List[str] = []
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.stealth = StealthManager()
        self.session_manager = SessionManager()
        self.max_retries = 3
        self.retry_delay = 5
        self.is_blocked = False
```

**Strengths:**
1. **Stealth features:** StealthManager applies browser fingerprinting countermeasures
2. **Session management:** SessionManager persists cookies/state across runs
3. **Proxy support:** Optional proxy integration (but see critical issue)
4. **Retry logic:** 3 retries with exponential backoff
5. **Blocking detection:** Detects Cloudflare, DataDome, CAPTCHA
6. **Captcha handling:** Basic wait-and-retry strategy
7. **Human-like behavior:** Scroll patterns, random delays
8. **Selector fallbacks:** Multiple CSS selectors for resilience
9. **Timeout protection:** All operations have timeouts
10. **Debug snapshots:** HTML snapshots for debugging

**Anti-Bot Measures:**
```python
# Stealth features (from StealthManager)
def get_browser_args(self):
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    ]
```

**Human-Like Behavior:**
```python
async def human_like_behavior(self):
    """Simulate complex human reading/browsing patterns."""
    scroll_pattern = [
        (random.randint(300, 800), random.uniform(1.0, 3.0)),
        (random.randint(-200, -50), random.uniform(0.5, 1.5)),  # Scroll up
        (random.randint(400, 900), random.uniform(2.0, 4.0)),
    ]
    
    for amount, pause in scroll_pattern:
        await self.tab.evaluate(f"window.scrollBy({{top: {amount}, behavior: 'smooth'}})")
        await asyncio.sleep(pause)
        
        if random.random() > 0.8:
            await asyncio.sleep(random.uniform(3, 6))  # Random pause
```

**Blocking Detection:**
```python
async def detect_blocking(self) -> bool:
    """Check for anti-bot markers in the current page."""
    content = await self.tab.get_content()
    markers = [
        "cf-challenge",      # Cloudflare
        "datadome",          # DataDome
        "captcha",           # Generic CAPTCHA
        "Access Denied",
        "403 Forbidden",
        "captcha-delivery"
    ]
    for marker in markers:
        if marker.lower() in content.lower():
            logger.error(f"[{self.name}] Anti-bot detected! (Marker: {marker})")
            self.is_blocked = True
            return True
    return False
```

**Limitations:**
- ⚠️ Blocking detection is string-based (can be bypassed)
- ⚠️ No IP reputation tracking
- ⚠️ No proxy health checking
- ⚠️ No circuit breaker for repeated failures
- ⚠️ Captcha handling is naive (just wait)
- ⚠️ No behavioral fingerprinting countermeasures

---

## 2. CRITICAL ISSUES

### 2.1 CRITICAL ISSUE #1: No Proxy Rotation in Production

**SEVERITY:** 🔴 CRITICAL - IP EXPOSURE RISK

**LOCATION:** `realestate_engine/scraping/proxy_manager.py`, `realestate_engine/utils/config.py`

**Problem:**
```python
# config.py:44-48
proxy_list: List[str] = field(default_factory=lambda: [
    p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()
])
residential_proxy_url: str = field(default_factory=lambda: os.getenv("RESIDENTIAL_PROXY_URL", ""))

# proxy_manager.py
class ProxyManager:
    def get_proxy(self) -> Optional[str]:
        """Returns a single proxy from list or residential proxy."""
        if self.residential_proxy_url:
            return self.residential_proxy_url
        if self.proxy_list:
            return random.choice(self.proxy_list)  # Random but no rotation logic
        return None  # NO PROXY = IP EXPOSURE
```

**Root Cause:**
- ProxyManager returns a single proxy (random from list or residential)
- No rotation during scraping session
- No failover if proxy fails
- No health checking of proxies
- No proxy tiering (free vs residential vs datacenter)
- If no proxy configured, scraping uses server's real IP

**Impact on Production:**
- **IP Blocking:** Portals can permanently block server IP
- **Legal Risk:** Scraping from fixed IP violates GDPR/ToS more visibly
- **Detection:** Easier to detect scraping patterns from single IP
- **Reliability:** Single point of failure
- **Scalability:** Cannot scale scraping with single IP
- **Commercial Viability:** Cannot sell as SaaS without proxy management

**Real-World Scenario:**
```
Day 1: Scraping works fine from IP 1.2.3.4
Day 2: Imovirtual detects high request rate from 1.2.3.4
Day 3: Imovirtual blocks 1.2.3.4 (403 Forbidden)
Day 4: All scraping fails, no fallback
Day 5: System down, revenue lost
```

**Refactor Suggestion - Professional Proxy Pool:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
import asyncio
import time
from loguru import logger

class ProxyTier(Enum):
    FREE = "free"
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"

@dataclass
class Proxy:
    url: str
    tier: ProxyTier
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0
    last_success: float = 0
    last_failure: float = 0
    is_banned: bool = False
    ban_until: float = 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    @property
    def is_available(self) -> bool:
        if self.is_banned:
            return time.time() > self.ban_until
        return True
    
    def mark_success(self):
        self.success_count += 1
        self.last_success = time.time()
        self.last_used = time.time()
    
    def mark_failure(self):
        self.failure_count += 1
        self.last_failure = time.time()
        self.last_used = time.time()
        
        # Auto-ban if failure rate > 80%
        if self.success_rate < 0.2 and (self.success_count + self.failure_count) > 5:
            self.is_banned = True
            self.ban_until = time.time() + 3600  # 1 hour cooldown
            logger.warning(f"Proxy {self.url} auto-banned for 1 hour")

class ProxyPool:
    """Professional proxy pool with tiering, health checking, and rotation."""
    
    def __init__(self):
        self.proxies: List[Proxy] = []
        self.current_index = 0
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from config and environment."""
        # Load free proxies
        free_proxies = config.proxy_list or []
        for url in free_proxies:
            self.proxies.append(Proxy(url=url, tier=ProxyTier.FREE))
        
        # Load residential proxy
        if config.residential_proxy_url:
            self.proxies.append(
                Proxy(url=config.residential_proxy_url, tier=ProxyTier.RESIDENTIAL)
            )
        
        # Load datacenter proxies (future)
        # ...
        
        logger.info(f"Loaded {len(self.proxies)} proxies: "
                   f"{sum(1 for p in self.proxies if p.tier == ProxyTier.FREE)} free, "
                   f"{sum(1 for p in self.proxies if p.tier == ProxyTier.RESIDENTIAL)} residential")
    
    def get_proxy(
        self,
        portal: str,
        risk_level: str = "medium",
        exclude_banned: bool = True
    ) -> Optional[Proxy]:
        """
        Get best proxy for the request.
        
        Args:
            portal: Target portal name
            risk_level: "low", "medium", "high" - determines proxy tier
            exclude_banned: Skip banned proxies
        """
        # Select tier based on risk level
        if risk_level == "high":
            preferred_tiers = [ProxyTier.RESIDENTIAL, ProxyTier.DATACENTER]
        elif risk_level == "medium":
            preferred_tiers = [ProxyTier.RESIDENTIAL, ProxyTier.DATACENTER, ProxyTier.FREE]
        else:
            preferred_tiers = [ProxyTier.FREE, ProxyTier.DATACENTER, ProxyTier.RESIDENTIAL]
        
        # Filter available proxies by tier
        available = [
            p for p in self.proxies
            if p.tier in preferred_tiers
            and (not exclude_banned or p.is_available)
        ]
        
        if not available:
            logger.error("No available proxies")
            return None
        
        # Sort by success rate (descending)
        available.sort(key=lambda p: p.success_rate, reverse=True)
        
        # Return best proxy
        return available[0]
    
    def mark_proxy_result(self, proxy: Proxy, success: bool):
        """Mark proxy result for health tracking."""
        if success:
            proxy.mark_success()
        else:
            proxy.mark_failure()
    
    def get_pool_stats(self) -> Dict:
        """Get pool statistics."""
        return {
            "total_proxies": len(self.proxies),
            "available_proxies": sum(1 for p in self.proxies if p.is_available),
            "banned_proxies": sum(1 for p in self.proxies if p.is_banned),
            "avg_success_rate": sum(p.success_rate for p in self.proxies) / len(self.proxies),
            "by_tier": {
                tier.value: sum(1 for p in self.proxies if p.tier == tier)
                for tier in ProxyTier
            }
        }

# Usage in spider
class BaseSpiderNodriver:
    def __init__(self, proxy_pool: ProxyPool):
        self.proxy_pool = proxy_pool
        self.current_proxy: Optional[Proxy] = None
    
    async def start_browser(self, headless: bool = True):
        proxy = self.proxy_pool.get_proxy(
            portal=self.name,
            risk_level="high"  # Use residential for high-risk portals
        )
        
        if not proxy:
            raise RuntimeError("No proxy available - cannot start scraping")
        
        self.current_proxy = proxy
        # ... start browser with proxy
```

**Additional Features Needed:**
1. **Proxy Health Checker:** Periodic health checks (every 5 minutes)
2. **Proxy Rotation:** Rotate proxy every N requests or time interval
3. **Proxy Warm-up:** Test proxy before using in production
4. **Proxy Reputation:** Track proxy performance per portal
5. **Proxy Auto-scaling:** Add/remove proxies based on demand

**Implementation Effort:** 5-7 days  
**Priority:** CRITICAL  
**Risk:** HIGH (core scraping logic)

**Cost Considerations:**
- Residential proxies: €50-200/month for 100-500 proxies
- Datacenter proxies: €10-50/month for 100 proxies
- Free proxies: Unreliable, high failure rate

**Recommendation:** 
- **Short-term:** Implement basic proxy pool with rotation
- **Medium-term:** Integrate residential proxy provider (Bright Data, Smartproxy)
- **Long-term:** Build auto-scaling proxy infrastructure

---

### 2.2 CRITICAL ISSUE #2: No Proxy in Production Configuration

**SEVERITY:** 🔴 CRITICAL - CONFIGURATION GAP

**LOCATION:** `realestate_engine/utils/config.py`

**Problem:**
```python
# config.py:44-48
proxy_list: List[str] = field(default_factory=lambda: [
    p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()
])
residential_proxy_url: str = field(default_factory=lambda: os.getenv("RESIDENTIAL_PROXY_URL", ""))

# If PROXY_LIST and RESIDENTIAL_PROXY_URL are not set:
# proxy_list = []
# residential_proxy_url = ""
# Result: No proxy used in production
```

**Root Cause:**
- No validation that proxy is configured in production
- No default proxy (empty string)
- No error if proxy not configured
- Developers may forget to set env vars

**Impact on Production:**
- **Silent failure:** Scraping runs without proxy, exposing IP
- **Deployment risk:** Production deploy without proxy configured
- **No safety net:** No runtime check for proxy availability

**Refactor Suggestion:**
```python
# config.py
@dataclass
class Config:
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    proxy_list: List[str] = field(default_factory=list)
    residential_proxy_url: str = field(default="")
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.environment == "production":
            if not self.residential_proxy_url and not self.proxy_list:
                raise RuntimeError(
                    "CRITICAL: Proxy must be configured in production. "
                    "Set RESIDENTIAL_PROXY_URL or PROXY_LIST environment variable."
                )
            
            logger.info(f"Production mode: Using {'residential' if self.residential_proxy_url else 'proxy list'}")
        
        # Warn in development if no proxy
        if self.environment == "development" and not self.residential_proxy_url and not self.proxy_list:
            logger.warning(
                "Development mode: No proxy configured. "
                "Scraping will use real IP (acceptable for dev, NOT for production)"
            )
```

**Implementation Effort:** 0.5 day  
**Priority:** CRITICAL  
**Risk:** LOW

---

## 3. HIGH PRIORITY ISSUES

### 3.1 HIGH PRIORITY ISSUE #1: No Proxy Health Checking

**SEVERITY:** 🟠 HIGH - RELIABILITY RISK

**LOCATION:** `realestate_engine/scraping/proxy_manager.py`

**Problem:**
```python
# Current implementation
class ProxyManager:
    def get_proxy(self) -> Optional[str]:
        if self.residential_proxy_url:
            return self.residential_proxy_url  # Returns proxy without checking if it works
        if self.proxy_list:
            return random.choice(self.proxy_list)  # Random choice, no health check
        return None
```

**Root Cause:**
- No health checking mechanism
- No tracking of proxy success/failure rates
- No removal of failed proxies from pool
- No periodic health verification

**Impact on Production:**
- **Failed requests:** Scraping fails silently if proxy is dead
- **Wasted time:** Retries on dead proxies waste time
- **Poor success rate:** Overall scraping success rate decreases
- **No visibility:** No metrics on proxy health

**Refactor Suggestion:**
```python
class ProxyHealthChecker:
    """Periodic health checking for proxies."""
    
    def __init__(self, proxy_pool: ProxyPool, check_interval: int = 300):
        self.proxy_pool = proxy_pool
        self.check_interval = check_interval  # 5 minutes
        self.check_url = "http://httpbin.org/ip"  # Simple health check
        self.is_running = False
    
    async def check_proxy(self, proxy: Proxy) -> bool:
        """Check if proxy is working."""
        try:
            async with httpx.AsyncClient(proxies=proxy.url, timeout=10.0) as client:
                resp = await client.get(self.check_url)
                if resp.status_code == 200:
                    proxy.mark_success()
                    logger.debug(f"Proxy {proxy.url} is healthy")
                    return True
        except Exception as e:
            proxy.mark_failure()
            logger.warning(f"Proxy {proxy.url} health check failed: {e}")
            return False
    
    async def check_all_proxies(self):
        """Check all proxies in pool."""
        tasks = [self.check_proxy(proxy) for proxy in self.proxy_pool.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy = sum(1 for r in results if r is True)
        logger.info(f"Health check complete: {healthy}/{len(results)} proxies healthy")
    
    async def start(self):
        """Start periodic health checking."""
        self.is_running = True
        logger.info(f"Starting proxy health checker (interval: {self.check_interval}s)")
        
        while self.is_running:
            await self.check_all_proxies()
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop health checking."""
        self.is_running = False
        logger.info("Proxy health checker stopped")

# Integration
proxy_pool = ProxyPool()
health_checker = ProxyHealthChecker(proxy_pool, check_interval=300)

# Start health checker in background
asyncio.create_task(health_checker.start())
```

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** MEDIUM

---

### 3.2 HIGH PRIORITY ISSUE #2: No Circuit Breaker Pattern

**SEVERITY:** 🟠 HIGH - CASCADING FAILURE RISK

**LOCATION:** `realestate_engine/scraping/spiders/base_spider_nodriver.py`

**Problem:**
```python
# Current retry logic
async def retry_operation(self, operation, *args, **kwargs):
    for attempt in range(self.max_retries):
        try:
            if self.is_blocked:
                await self.handle_captcha()
                await self.rotate_proxy()
            return await operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(self.retry_delay * (attempt + 1))
    raise Exception(f"Operation failed after {self.max_retries} attempts")
```

**Root Cause:**
- No circuit breaker to stop trying after N consecutive failures
- No cooldown period after failures
- No automatic recovery after cooldown
- Keeps retrying even if portal is permanently down

**Impact on Production:**
- **Resource waste:** Continues retrying dead endpoints
- **Cascading failures:** Failed spider blocks entire pipeline
- **No automatic recovery:** Manual intervention required
- **Poor user experience:** System appears hung

**Refactor Suggestion:**
```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, stop trying
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold  # Failures before opening
        self.recovery_timeout = recovery_timeout    # Seconds to wait before retry
        self.expected_exception = expected_exception
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    def call(self, func):
        """Decorator to wrap function with circuit breaker."""
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker: HALF_OPEN - attempting reset")
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= 3:  # 3 successful calls to close circuit
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED - service recovered")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker: OPEN - {self.failure_count} failures "
                f"(threshold: {self.failure_threshold})"
            )

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

# Usage in spider
class BaseSpiderNodriver:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300,  # 5 minutes
            expected_exception=(TimeoutError, ConnectionError)
        )
    
    @circuit_breaker.call
    async def parse_page(self, page_num: int) -> List[Dict]:
        # This will be protected by circuit breaker
        pass
```

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** MEDIUM

---

### 3.3 HIGH PRIORITY ISSUE #3: No Per-Portal Rate Limiting

**SEVERITY:** 🟠 HIGH - BAN RISK

**LOCATION:** `realestate_engine/scraping/spider_manager.py`

**Problem:**
```python
# SpiderManager runs all spiders without per-portal rate limiting
async def run_all_cycle(self, active_portals: List[str]) -> Dict[str, int]:
    summary = {}
    for portal in active_portals:
        spider = self.spiders[portal]
        results = await spider.run(max_pages=5)
        summary[portal] = len(results)
    return summary
```

**Root Cause:**
- No rate limiting per portal
- All portals scraped at same pace
- Some portals are more aggressive than others (Casa Sapo is very aggressive)
- No adaptive rate limiting based on response

**Impact on Production:**
- **Portal bans:** Aggressive portals will ban the IP
- **Inefficient scraping:** Conservative rate limits slow down lenient portals
- **No adaptability:** Cannot adjust based on portal response
- **Wasted resources:** Scraping blocked portals wastes time

**Portal Aggressiveness (Observed):**
| Portal | Aggressiveness | Recommended Delay | Notes |
|--------|---------------|-------------------|-------|
| Casa Sapo | VERY HIGH | 10-20s | Will ban quickly |
| Idealista | HIGH | 5-10s | Cloudflare protection |
| Imovirtual | LOW | 1-3s | Tolerant (direct fetch) |
| REMAX | MEDIUM | 3-5s | Moderate protection |
| ERA | MEDIUM | 3-5s | Moderate protection |
| Supercasa | MEDIUM | 3-5s | Moderate protection |
| Century21 | LOW | 2-4s | Lenient |
| OLX | HIGH | 5-8s | Aggressive |

**Refactor Suggestion:**
```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class PortalConfig:
    name: str
    base_delay: float  # Base delay in seconds
    max_delay: float    # Maximum delay in seconds
    jitter: float       # Jitter factor (0-1)
    requests_per_minute: int  # Max requests per minute
    ban_threshold: int  # Failures before considering banned
    recovery_time: int  # Seconds to wait after ban

# Portal configurations
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
    # ... other portals
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
            logger.warning(f"No config for portal {portal}")
            return True
        
        # Check if banned
        if portal in self.ban_until:
            if time.time() < self.ban_until[portal]:
                logger.warning(f"Portal {portal} is banned until {self.ban_until[portal]}")
                return False
            else:
                # Ban expired
                del self.ban_until[portal]
                self.failure_counts[portal] = 0
        
        # Calculate delay
        base_delay = config.base_delay
        if portal in self.failure_counts:
            # Exponential backoff based on failures
            backoff_factor = min(2 ** self.failure_counts[portal], 4)
            base_delay = min(base_delay * backoff_factor, config.max_delay)
        
        # Add jitter
        import random
        delay = base_delay * (1 - config.jitter + random.random() * 2 * config.jitter)
        
        # Enforce requests per minute
        if portal in self.last_request_times:
            time_since_last = time.time() - self.last_request_times[portal]
            min_interval = 60 / config.requests_per_minute
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
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
            logger.error(f"Portal {portal} banned for {config.recovery_time}s due to {self.failure_counts[portal]} failures")
    
    def record_success(self, portal: str):
        """Record a success for the portal."""
        self.failure_counts[portal] = 0

# Usage in SpiderManager
class SpiderManager:
    def __init__(self):
        self.rate_limiter = PortalRateLimiter()
    
    async def run_all_cycle(self, active_portals: List[str]) -> Dict[str, int]:
        summary = {}
        for portal in active_portals:
            if not await self.rate_limiter.wait_if_needed(portal):
                logger.error(f"Skipping {portal} - rate limited")
                summary[portal] = 0
                continue
            
            try:
                spider = self.spiders[portal]
                results = await spider.run(max_pages=5)
                summary[portal] = len(results)
                self.rate_limiter.record_success(portal)
            except Exception as e:
                logger.error(f"Failed to scrape {portal}: {e}")
                self.rate_limiter.record_failure(portal)
                summary[portal] = 0
        
        return summary
```

**Implementation Effort:** 3 days  
**Priority:** HIGH  
**Risk:** MEDIUM

---

### 3.4 HIGH PRIORITY ISSUE #4: No Scraping Health Monitoring

**SEVERITY:** 🟠 HIGH - NO VISIBILITY

**LOCATION:** Missing component

**Problem:**
- No metrics on scraping success rate per portal
- No metrics on scraping duration per portal
- No metrics on proxy health
- No alerts for scraping failures
- No dashboard for scraping health

**Impact on Production:**
- **No visibility:** Cannot tell if scraping is working
- **Silent failures:** Scraping may fail without notification
- **No debugging:** Difficult to troubleshoot issues
- **No optimization:** Cannot identify slow portals

**Refactor Suggestion:**
```python
from realestate_engine.monitoring.metrics import MetricsCollector

class ScrapingHealthMonitor:
    """Monitor scraping health and metrics."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
    
    def record_scrape_start(self, portal: str):
        """Record start of scraping session."""
        self.metrics.scraping_session_start.labels(portal=portal).inc()
    
    def record_scrape_end(self, portal: str, duration: float, success: bool, listings_count: int):
        """Record end of scraping session."""
        self.metrics.scraping_session_duration.labels(portal=portal).observe(duration)
        
        if success:
            self.metrics.scraping_session_success.labels(portal=portal).inc()
            self.metrics.listings_scraped.labels(portal=portal).inc(listings_count)
        else:
            self.metrics.scraping_session_failure.labels(portal=portal).inc()
    
    def record_proxy_use(self, proxy_url: str, success: bool):
        """Record proxy usage."""
        if success:
            self.metrics.proxy_success.labels(proxy=proxy_url).inc()
        else:
            self.metrics.proxy_failure.labels(proxy=proxy_url).inc()
    
    def record_blocking_detected(self, portal: str, blocker_type: str):
        """Record anti-bot detection."""
        self.metrics.anti_bot_detected.labels(portal=portal, blocker=blocker_type).inc()
    
    def get_health_report(self) -> Dict:
        """Generate health report."""
        return {
            "scraping_sessions": self.metrics.scraping_session_start._value.get(),
            "success_rate": self._calculate_success_rate(),
            "listings_per_minute": self._calculate_listings_per_minute(),
            "proxy_health": self._get_proxy_health(),
            "blocked_portals": self._get_blocked_portals()
        }
    
    def _calculate_success_rate(self) -> float:
        total = self.metrics.scraping_session_success._value.get() + self.metrics.scraping_session_failure._value.get()
        if total == 0:
            return 1.0
        return self.metrics.scraping_session_success._value.get() / total

# Add to MetricsCollector
class MetricsCollector:
    def __init__(self):
        # ... existing metrics ...
        
        # Scraping health metrics
        self.scraping_session_start = Counter(
            'scraping_session_start_total',
            'Total scraping sessions started',
            ['portal']
        )
        self.scraping_session_success = Counter(
            'scraping_session_success_total',
            'Total scraping sessions succeeded',
            ['portal']
        )
        self.scraping_session_failure = Counter(
            'scraping_session_failure_total',
            'Total scraping sessions failed',
            ['portal']
        )
        self.scraping_session_duration = Histogram(
            'scraping_session_duration_seconds',
            'Scraping session duration',
            ['portal']
        )
        self.listings_scraped = Counter(
            'listings_scraped_total',
            'Total listings scraped',
            ['portal']
        )
        self.proxy_success = Counter(
            'proxy_success_total',
            'Proxy requests succeeded',
            ['proxy']
        )
        self.proxy_failure = Counter(
            'proxy_failure_total',
            'Proxy requests failed',
            ['proxy']
        )
        self.anti_bot_detected = Counter(
            'anti_bot_detected_total',
            'Anti-bot detection events',
            ['portal', 'blocker']
        )
```

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** LOW

---

## 4. MEDIUM PRIORITY ISSUES

### 4.1 MEDIUM PRIORITY ISSUE #1: Captcha Handling is Naive

**SEVERITY:** 🟡 MEDIUM - LOW SUCCESS RATE

**LOCATION:** `realestate_engine/scraping/spiders/base_spider_nodriver.py`

**Problem:**
```python
async def handle_captcha(self) -> bool:
    """Try to handle captcha by waiting and retrying."""
    logger.warning(f"[{self.name}] Captcha detected, waiting 30 seconds...")
    await asyncio.sleep(30)
    if await self.detect_blocking():
        logger.error(f"[{self.name}] Captcha still present after wait")
        return False
    logger.info(f"[{self.name}] Captcha resolved")
    return True
```

**Root Cause:**
- Just waits 30 seconds and hopes captcha resolves
- No captcha solving service integration
- No captcha type detection (Cloudflare vs reCAPTCHA vs hCaptcha)
- No fallback strategies

**Impact on Production:**
- **Low success rate:** Most captchas won't resolve by waiting
- **Wasted time:** 30 seconds wasted per captcha
- **Manual intervention:** Requires human to solve captchas

**Refactor Suggestion:**
```python
class CaptchaSolver:
    """Integration with captcha solving services."""
    
    def __init__(self, api_key: str, service: str = "2captcha"):
        self.api_key = api_key
        self.service = service
    
    async def solve_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve reCAPTCHA using external service."""
        # Implementation depends on service
        # Example with 2captcha:
        # 1. Submit captcha
        # 2. Poll for result
        # 3. Return solution token
        pass
    
    async def solve_cloudflare(self, page_url: str) -> bool:
        """Solve Cloudflare challenge."""
        # Cloudflare challenges are harder
        # May require browser automation with specific techniques
        pass

class BaseSpiderNodriver:
    def __init__(self, captcha_solver: Optional[CaptchaSolver] = None):
        self.captcha_solver = captcha_solver
    
    async def handle_captcha(self) -> bool:
        """Try to handle captcha with multiple strategies."""
        logger.warning(f"[{self.name}] Captcha detected")
        
        # Strategy 1: Wait and retry (naive but free)
        await asyncio.sleep(30)
        if not await self.detect_blocking():
            logger.info(f"[{self.name}] Captcha resolved by waiting")
            return True
        
        # Strategy 2: Use captcha solver if available
        if self.captcha_solver:
            try:
                # Detect captcha type
                captcha_type = self._detect_captcha_type()
                
                if captcha_type == "recaptcha":
                    site_key = self._extract_recaptcha_site_key()
                    token = await self.captcha_solver.solve_recaptcha(site_key, self.tab.get_url())
                    if token:
                        await self._inject_recaptcha_token(token)
                        await asyncio.sleep(2)
                        if not await self.detect_blocking():
                            logger.info(f"[{self.name}] Captcha solved via service")
                            return True
                elif captcha_type == "cloudflare":
                    success = await self.captcha_solver.solve_cloudflare(self.tab.get_url())
                    if success:
                        logger.info(f"[{self.name}] Cloudflare solved via service")
                        return True
            except Exception as e:
                logger.error(f"Captcha solver failed: {e}")
        
        # Strategy 3: Rotate proxy and retry
        logger.warning(f"[{self.name}] All captcha strategies failed, rotating proxy")
        await self.rotate_proxy()
        
        return False
    
    def _detect_captcha_type(self) -> str:
        """Detect type of captcha."""
        content = await self.tab.get_content()
        
        if "recaptcha" in content.lower():
            return "recaptcha"
        elif "cf-challenge" in content.lower() or "data-dome" in content.lower():
            return "cloudflare"
        elif "hcaptcha" in content.lower():
            return "hcaptcha"
        
        return "unknown"
```

**Implementation Effort:** 3-4 days  
**Priority:** MEDIUM  
**Risk:** MEDIUM (requires third-party service)

**Cost Considerations:**
- 2captcha: $2-3 per 1000 captchas
- Anti-Captcha: $0.5-1 per 1000 captchas
- DeathByCaptcha: $1-2 per 1000 captchas

---

### 4.2 MEDIUM PRIORITY ISSUE #2: No User-Agent Rotation

**SEVERITY:** 🟡 MEDIUM - DETECTION RISK

**LOCATION:** `realestate_engine/scraping/spiders/imovirtual_nextdata_spider.py`

**Problem:**
```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    # Static user-agent
}
```

**Root Cause:**
- Single user-agent for all requests
- Easy to detect scraping pattern
- No rotation to blend in with real users

**Impact on Production:**
- **Detection:** Easier to detect as scraper
- **Blocking:** Higher chance of IP ban
- **Lower success rate:** Portals may block known scraping user-agents

**Refactor Suggestion:**
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # ... more user-agents
]

class UserAgentRotator:
    """Rotate user-agents to blend in with real users."""
    
    def __init__(self, user_agents: List[str] = None):
        self.user_agents = user_agents or USER_AGENTS
        self.current_index = 0
    
    def get_user_agent(self) -> str:
        """Get next user-agent in rotation."""
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua
    
    def get_random_user_agent(self) -> str:
        """Get random user-agent."""
        import random
        return random.choice(self.user_agents)

# Usage
class ImovirtualNextDataSpider:
    def __init__(self):
        self.ua_rotator = UserAgentRotator()
    
    async def _fetch_next_data(self, client, url, page_num):
        headers = self.HEADERS.copy()
        headers["User-Agent"] = self.ua_rotator.get_random_user_agent()
        resp = await client.get(url, headers=headers)
```

**Implementation Effort:** 0.5 day  
**Priority:** MEDIUM  
**Risk:** LOW

---

### 4.3 MEDIUM PRIORITY ISSUE #3: No Session Persistence

**SEVERITY:** 🟡 MEDIUM - STATE LOSS

**LOCATION:** `realestate_engine/scraping/session_manager.py`

**Problem:**
```python
class SessionManager:
    def save_session(self, tab, spider_name):
        """Save session cookies to file."""
        # Saves to local file
        # Not distributed across multiple workers
    
    def restore_session(self, tab, spider_name):
        """Restore session cookies from file."""
        # Loads from local file
        # Not distributed
```

**Root Cause:**
- Sessions saved to local files
- No distributed session storage (Redis)
- Multiple workers can't share sessions
- No session expiration

**Impact on Production:**
- **Inconsistent state:** Multiple workers have different sessions
- **No scalability:** Cannot scale horizontally
- **Session loss:** Sessions lost if worker restarts

**Refactor Suggestion:**
```python
class DistributedSessionManager:
    """Distributed session management using Redis."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_ttl = 3600  # 1 hour
    
    async def save_session(self, spider_name: str, cookies: List[Dict]):
        """Save session to Redis."""
        key = f"session:{spider_name}"
        await self.redis.setex(
            key,
            self.session_ttl,
            json.dumps(cookies)
        )
        logger.info(f"Session saved for {spider_name}")
    
    async def restore_session(self, spider_name: str) -> Optional[List[Dict]]:
        """Restore session from Redis."""
        key = f"session:{spider_name}"
        data = await self.redis.get(key)
        
        if data:
            cookies = json.loads(data)
            logger.info(f"Session restored for {spider_name}")
            return cookies
        
        logger.info(f"No session found for {spider_name}")
        return None
    
    async def delete_session(self, spider_name: str):
        """Delete session from Redis."""
        key = f"session:{spider_name}"
        await self.redis.delete(key)
        logger.info(f"Session deleted for {spider_name}")
```

**Implementation Effort:** 2 days  
**Priority:** MEDIUM  
**Risk:** MEDIUM (requires Redis)

---

### 4.4 Additional Medium Priority Issues

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 5 | No request signature randomization | All spiders | MEDIUM | 1 day | MEDIUM |
| 6 | No browser fingerprinting countermeasures | BaseSpiderNodriver | MEDIUM | 2 days | MEDIUM |
| 7 | No scraping queue management | SpiderManager | MEDIUM | 3 days | MEDIUM |
| 8 | No spider health checks | All spiders | LOW | 1 day | MEDIUM |

---

## 5. LOW PRIORITY ISSUES

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 1 | Selector fallbacks not used consistently | BaseSpiderNodriver | LOW | 0.5 day | LOW |
| 2 | Debug snapshots not persisted | BaseSpiderNodriver | LOW | 0.5 day | LOW |
| 3 | No scraping statistics dashboard | Missing | LOW | 2 days | LOW |

---

## 6. REFACTOR ROADMAP

### Phase 1: Critical Fixes (Week 1)
- [ ] Add proxy validation in config (production check)
- [ ] Implement basic proxy pool with rotation
- [ ] Add proxy health checking
- [ ] Integrate residential proxy provider

### Phase 2: High Priority (Week 2)
- [ ] Implement circuit breaker pattern
- [ ] Add per-portal rate limiting
- [ ] Implement scraping health monitoring
- [ ] Add user-agent rotation

### Phase 3: Medium Priority (Week 3)
- [ ] Improve captcha handling
- [ ] Implement distributed session management
- [ ] Add request signature randomization
- [ ] Add browser fingerprinting countermeasures

### Phase 4: Low Priority (Week 4)
- [ ] Use selector fallbacks consistently
- [ ] Persist debug snapshots
- [ ] Create scraping statistics dashboard

---

## 7. PRODUCTION READINESS SCORE

**Scraping Audit Score: 72/100**

**Breakdown:**
- Architecture: 80/100 (excellent dual approach)
- Anti-Bot Measures: 70/100 (good but basic)
- Proxy Management: 40/100 (critical gap)
- Retry Logic: 75/100 (good but no circuit breaker)
- Rate Limiting: 50/100 (no per-portal limits)
- Health Monitoring: 30/100 (no visibility)
- Session Management: 65/100 (local only, not distributed)

**Recommendation:** Address proxy management and rate limiting before production deployment. Without proxy rotation, system is not production-ready.

---

**End of Phase 2: Scraping Audit**
