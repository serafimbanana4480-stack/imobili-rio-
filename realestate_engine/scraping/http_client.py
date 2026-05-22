"""HTTP client helpers — UA rotation, realistic headers, session reuse.

Provides:
- ``pick_user_agent()`` — random UA from an up-to-date pool.
- ``default_headers(referer=?)`` — a realistic Chrome header set.
- ``SmartHttpClient`` — thin wrapper around ``httpx.AsyncClient`` that:
    * rotates proxies via ``ProxyManager``
    * applies the portal strategy (direct / proxy / hybrid)
    * auto-retries on failure with a *different* proxy
    * measures latency and reports success/failure back to the manager

This is deliberately small: spiders stay in control of parsing, we only
provide resilient transport.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import httpx
from loguru import logger

from realestate_engine.scraping.proxy_manager import ProxyManager

try:
    from curl_cffi.requests import AsyncSession as CurlSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    logger.warning("curl-cffi not available — TLS fingerprinting disabled. Install: pip install curl-cffi")


USER_AGENTS: list[str] = [
    # Chrome — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    # Chrome — macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # Edge — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    # Firefox — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]


def pick_user_agent() -> str:
    return random.choice(USER_AGENTS)


def default_headers(referer: Optional[str] = None, lang: str = "pt-PT,pt;q=0.9,en;q=0.8") -> Dict[str, str]:
    h: Dict[str, str] = {
        "User-Agent": pick_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": lang,
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if referer is None else "same-origin",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        h["Referer"] = referer
    return h


# Hints that a response is effectively a block page, independent of HTTP status.
BLOCK_HINTS_BYTES = (
    b"captcha",
    b"datadome",
    b"<title>Attention Required",
    b"cf-browser-verification",
    b"px-captcha",
    b"Access Denied",
)


@dataclass
class FetchResult:
    ok: bool
    status_code: Optional[int]
    content: bytes
    latency_ms: float
    proxy_used: Optional[str]
    attempts: int
    error: Optional[str] = None

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


def _looks_blocked(resp: httpx.Response) -> bool:
    if resp.status_code in (403, 429, 503):
        return True
    snippet = (resp.content or b"")[:8192]
    low = snippet.lower()
    return any(h.lower() in low for h in (b.lower() for b in BLOCK_HINTS_BYTES))


_CURL_IMPERSONATIONS = [
    "chrome120", "chrome124", "chrome131", "chrome136",
    "edge101", "edge120",
]


class SmartHttpClient:
    """Resilient HTTP client with portal-aware proxy usage and TLS fingerprinting.

    When curl-cffi is available, requests are made with Chrome's exact TLS
    ClientHello (JA3/JA4) fingerprint, defeating TLS-aware WAFs such as
    Cloudflare and DataDome. Falls back gracefully to plain httpx.
    """

    def __init__(
        self,
        portal: str,
        proxy_manager: Optional[ProxyManager] = None,
        max_retries: int = 3,
        per_request_timeout: float = 25.0,
        delay_range: tuple[float, float] = (1.5, 3.5),
        use_tls_fingerprinting: bool = True,
    ):
        self.portal = portal
        self.proxy_manager = proxy_manager or ProxyManager()
        self.max_retries = max_retries
        self.per_request_timeout = per_request_timeout
        self.delay_range = delay_range
        self.strategy = ProxyManager.strategy_for(portal)
        self.use_tls_fingerprinting = use_tls_fingerprinting and CURL_CFFI_AVAILABLE
        self._impersonation = random.choice(_CURL_IMPERSONATIONS)

    async def _fetch_with_curl(self, url: str, headers: Dict[str, str], proxy: Optional[str]) -> tuple:
        """Fetch using curl-cffi with Chrome TLS impersonation."""
        curl_kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.per_request_timeout,
            "allow_redirects": True,
            "impersonate": self._impersonation,
        }
        if proxy:
            curl_kwargs["proxies"] = {"https": proxy, "http": proxy}
        async with CurlSession() as session:
            resp = await session.get(url, **curl_kwargs)
        return resp.status_code, resp.content

    async def _fetch_with_httpx(self, url: str, headers: Dict[str, str], proxy: Optional[str]) -> tuple:
        """Fetch using plain httpx (fallback)."""
        client_kwargs: Dict[str, Any] = dict(
            headers=headers,
            timeout=httpx.Timeout(self.per_request_timeout, connect=10.0),
            follow_redirects=True,
            http2=False,
        )
        if proxy:
            client_kwargs["proxy"] = proxy
        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.get(url)
        return resp.status_code, resp.content

    async def fetch(self, url: str, referer: Optional[str] = None) -> FetchResult:
        """Fetch ``url`` with retry + proxy rotation per the portal strategy.

        Transport priority:
          1. curl-cffi with Chrome TLS impersonation (if available)
          2. httpx fallback

        Retry policy:
          - ``direct``: retry directly (no proxy) up to ``max_retries``.
          - ``proxy``:  retry using a different proxy each time.
          - ``hybrid``: first try direct; on block/failure fall back to proxies.
        """
        last_error: Optional[str] = None
        attempts = 0
        attempted_direct = False

        for attempt in range(1, self.max_retries + 1):
            attempts = attempt

            if self.strategy == "direct":
                proxy = None
            elif self.strategy == "proxy":
                proxy = self.proxy_manager.get_proxy(self.portal)
                if proxy is None:
                    return FetchResult(
                        ok=False, status_code=None, content=b"", latency_ms=0.0,
                        proxy_used=None, attempts=attempts,
                        error="proxy_required_but_none_available",
                    )
            else:  # hybrid
                if not attempted_direct:
                    proxy = None
                    attempted_direct = True
                else:
                    proxy = self.proxy_manager.get_proxy(self.portal)

            headers = default_headers(referer=referer)

            start = time.perf_counter()
            try:
                if self.use_tls_fingerprinting:
                    status_code, content = await self._fetch_with_curl(url, headers, proxy)
                else:
                    status_code, content = await self._fetch_with_httpx(url, headers, proxy)
            except Exception as e:
                latency_ms = (time.perf_counter() - start) * 1000.0
                last_error = f"{e.__class__.__name__}"
                if proxy:
                    self.proxy_manager.mark_failed(proxy, error=last_error)
                await self._pace()
                continue

            latency_ms = (time.perf_counter() - start) * 1000.0

            snippet = (content or b"")[:8192].lower()
            is_blocked = status_code in (403, 429, 503) or any(
                h.lower() in snippet for h in (b.lower() for b in BLOCK_HINTS_BYTES)
            )

            if is_blocked:
                last_error = f"blocked_http_{status_code}"
                if proxy:
                    self.proxy_manager.mark_failed(proxy, error=last_error)
                logger.info(
                    f"[{self.portal}] attempt {attempt} blocked "
                    f"(status={status_code}, proxy={'yes' if proxy else 'direct'}, "
                    f"tls={'curl' if self.use_tls_fingerprinting else 'httpx'}, {latency_ms:.0f}ms)"
                )
                await self._pace()
                continue

            if status_code >= 400:
                last_error = f"http_{status_code}"
                if proxy:
                    self.proxy_manager.mark_failed(proxy, error=last_error)
                await self._pace()
                continue

            if proxy:
                self.proxy_manager.mark_success(proxy, latency_ms=latency_ms)

            return FetchResult(
                ok=True,
                status_code=status_code,
                content=content,
                latency_ms=latency_ms,
                proxy_used=proxy,
                attempts=attempts,
            )

        return FetchResult(
            ok=False, status_code=None, content=b"", latency_ms=0.0,
            proxy_used=None, attempts=attempts, error=last_error or "unknown",
        )

    async def _pace(self) -> None:
        await asyncio.sleep(random.uniform(*self.delay_range))
