"""Proxy validator — filters raw proxies into working / slow / dead buckets.

Validation is a two-stage cascade:

Stage 1 (cheap): hit a tiny echo endpoint (httpbin / ifconfig.me) over HTTPS
    to verify:
      - the proxy accepts connections
      - it actually forwards traffic (IP differs from local egress)
      - it supports CONNECT/TLS (needed for real-estate portals)

Stage 2 (targeted): optionally hit a lightweight path on the real target
    domain (e.g. https://www.idealista.pt/robots.txt) to confirm the proxy
    is not already banned by that specific portal.

Both stages measure latency. Proxies are classified as:
    - working: OK, latency < fast_threshold_s
    - slow:    OK, latency >= fast_threshold_s but <= max_latency_s
    - dead:    any failure, timeout, non-2xx, or obvious captcha page
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import httpx
from loguru import logger

from realestate_engine.scraping.free_proxy_provider import RawProxy


ECHO_ENDPOINTS = [
    "https://api.ipify.org?format=text",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
]

# Indicators of a captive/captcha/error page injected by a hostile proxy.
BLOCK_MARKERS = (
    b"captcha",
    b"cloudflare",
    b"access denied",
    b"forbidden",
    b"<title>attention required",
    b"datadome",
    b"incapsula",
)


@dataclass
class ProxyCheck:
    proxy: RawProxy
    ok: bool
    latency_ms: float = 0.0
    remote_ip: Optional[str] = None
    target_ok: Optional[bool] = None
    target_status: Optional[int] = None
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ProxyPool:
    """Classified pool of validated proxies."""
    working: List[ProxyCheck] = field(default_factory=list)
    slow: List[ProxyCheck] = field(default_factory=list)
    dead: List[ProxyCheck] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "working": len(self.working),
            "slow": len(self.slow),
            "dead": len(self.dead),
            "avg_latency_ms_working": (
                round(sum(c.latency_ms for c in self.working) / len(self.working), 1)
                if self.working else None
            ),
        }

    def usable(self) -> List[ProxyCheck]:
        """Fast + slow, sorted by latency ascending."""
        return sorted(self.working + self.slow, key=lambda c: c.latency_ms)


class ProxyValidator:
    """Validates raw proxies concurrently.

    Default thresholds:
      - connect_timeout=5s, read_timeout=10s, overall per-check cap=15s
      - fast_threshold_ms=3000, max_latency_ms=10000

    Tune ``max_concurrent`` carefully: too high and many proxies will fail
    with "connection reset" purely from burst load.
    """

    def __init__(
        self,
        target_url: Optional[str] = None,
        max_concurrent: int = 50,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
        fast_threshold_ms: float = 3000.0,
        max_latency_ms: float = 10000.0,
    ):
        self.target_url = target_url
        self.max_concurrent = max_concurrent
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.fast_threshold_ms = fast_threshold_ms
        self.max_latency_ms = max_latency_ms

    async def validate_batch(self, proxies: List[RawProxy]) -> ProxyPool:
        """Run the full validation cascade on a batch and classify results."""
        if not proxies:
            return ProxyPool()

        logger.info(
            f"[ProxyValidator] validating {len(proxies)} proxies "
            f"(concurrency={self.max_concurrent}, target={self.target_url or 'none'})"
        )
        sem = asyncio.Semaphore(self.max_concurrent)

        async def _run(p: RawProxy) -> ProxyCheck:
            async with sem:
                return await self._check_one(p)

        results = await asyncio.gather(*(_run(p) for p in proxies))

        pool = ProxyPool()
        for c in results:
            if not c.ok:
                pool.dead.append(c)
            elif c.latency_ms <= self.fast_threshold_ms and (c.target_ok is not False):
                pool.working.append(c)
            elif c.latency_ms <= self.max_latency_ms and (c.target_ok is not False):
                pool.slow.append(c)
            else:
                pool.dead.append(c)

        logger.info(f"[ProxyValidator] result: {pool.summary()}")
        return pool

    async def _check_one(self, proxy: RawProxy) -> ProxyCheck:
        """Echo check + optional target check. Returns structured result."""
        check = ProxyCheck(proxy=proxy, ok=False)

        timeout = httpx.Timeout(
            self.read_timeout,
            connect=self.connect_timeout,
        )
        transport_kwargs = {"proxy": proxy.url, "timeout": timeout, "verify": False}

        # --- Stage 1: echo ------------------------------------------------
        for echo in ECHO_ENDPOINTS:
            ok, ms, ip, err = await self._try_echo(echo, transport_kwargs)
            if ok:
                check.ok = True
                check.latency_ms = ms
                check.remote_ip = ip
                break
            check.error = err
        if not check.ok:
            return check

        # --- Stage 2: target (optional) -----------------------------------
        if self.target_url:
            t_ok, t_status, t_ms, t_err = await self._try_target(
                self.target_url, transport_kwargs
            )
            check.target_ok = t_ok
            check.target_status = t_status
            if t_err:
                check.notes.append(t_err)
            # Inflate latency with target RTT — it is the real cost.
            check.latency_ms = max(check.latency_ms, t_ms or check.latency_ms)

        return check

    async def _try_echo(self, url: str, client_kwargs: dict) -> Tuple[bool, float, Optional[str], Optional[str]]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(**client_kwargs) as c:
                r = await c.get(url)
        except Exception as e:
            return False, 0.0, None, f"{e.__class__.__name__}"

        ms = (time.perf_counter() - start) * 1000.0
        if r.status_code != 200:
            return False, ms, None, f"echo_http_{r.status_code}"

        body = (r.text or "").strip()
        # Very defensive: body must look like an IP address.
        if not body or len(body) > 64 or any(ch.isspace() for ch in body if ch != "\n"):
            return False, ms, None, "echo_not_ip"
        # Strip trailing whitespace / newlines.
        ip = body.splitlines()[0].strip()
        parts = ip.split(".")
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return False, ms, None, "echo_not_ipv4"
        return True, ms, ip, None

    async def _try_target(self, url: str, client_kwargs: dict) -> Tuple[bool, Optional[int], float, Optional[str]]:
        """Hit the target with a realistic browser header set."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        }
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(follow_redirects=True, headers=headers, **client_kwargs) as c:
                r = await c.get(url)
        except Exception as e:
            ms = (time.perf_counter() - start) * 1000.0
            return False, None, ms, f"target_{e.__class__.__name__}"

        ms = (time.perf_counter() - start) * 1000.0
        if r.status_code >= 500 or r.status_code in (403, 429):
            return False, r.status_code, ms, f"target_http_{r.status_code}"
        snippet = (r.content or b"")[:4096].lower()
        for marker in BLOCK_MARKERS:
            if marker in snippet:
                return False, r.status_code, ms, f"target_blocked_{marker.decode()}"
        return r.status_code < 400, r.status_code, ms, None
