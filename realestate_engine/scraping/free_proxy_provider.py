"""Free proxy provider — fetches proxy lists from multiple public sources.

Fetches, parses, and deduplicates proxies from a curated list of
community-maintained free proxy feeds. Nothing is validated here;
use ``ProxyValidator`` to filter live proxies from this raw pool.

Sources are ranked by historical reliability. Each source is fetched
independently; failures are logged but never halt the aggregation.

NOTE: Free proxies are, by their nature, slow, unstable, and often
dead on arrival. Expect <10 % of fetched proxies to pass validation
against a real-estate portal. This is a best-effort layer.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple

import httpx
from loguru import logger


# Each source yields plain text "ip:port" lines (one per line) unless noted.
# Ordered by empirical reliability (monosans / TheSpeedX / proxifly top the list
# as of 2025-Q2 community benchmarks).
FREE_PROXY_SOURCES: List[Tuple[str, str, str]] = [
    # (name, url, protocol)
    ("monosans-http",      "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",            "http"),
    ("monosans-socks4",    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",          "socks4"),
    ("monosans-socks5",    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",          "socks5"),
    ("thespeedx-http",     "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",                  "http"),
    ("thespeedx-socks4",   "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",                "socks4"),
    ("thespeedx-socks5",   "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",                "socks5"),
    ("clarketm",           "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",         "http"),
    ("proxyscrape-http",   "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all",     "http"),
    ("proxyscrape-socks4", "https://api.proxyscrape.com/v2/?request=get&protocol=socks4&timeout=10000&country=all",   "socks4"),
    ("proxyscrape-socks5", "https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=10000&country=all",   "socks5"),
    ("proxifly-http",      "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",   "http"),
    ("proxifly-socks4",    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt", "socks4"),
    ("proxifly-socks5",    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt", "socks5"),
    ("mmpx12",             "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",                      "http"),
    ("jetkai",             "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt", "http"),
]

_ADDR_RE = re.compile(r"^\s*(?:([a-z0-9]+)://)?([0-9]{1,3}(?:\.[0-9]{1,3}){3}):([0-9]{2,5})\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class RawProxy:
    """Raw (unvalidated) proxy record."""
    protocol: str   # http | socks4 | socks5
    host: str
    port: int
    source: str

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def __str__(self) -> str:  # pragma: no cover
        return self.url


class FreeProxyProvider:
    """Fetches and deduplicates raw proxies from free public sources."""

    def __init__(
        self,
        sources: Optional[Iterable[Tuple[str, str, str]]] = None,
        request_timeout: float = 15.0,
        max_concurrent: int = 6,
    ):
        self.sources = list(sources) if sources is not None else list(FREE_PROXY_SOURCES)
        self.request_timeout = request_timeout
        self._sem = asyncio.Semaphore(max_concurrent)

    async def fetch_all(self) -> List[RawProxy]:
        """Fetch every configured source concurrently and return unique proxies."""
        logger.info(f"[FreeProxyProvider] fetching {len(self.sources)} sources…")
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.request_timeout),
            follow_redirects=True,
            headers={"User-Agent": "RealEstateEngine/1.0 (+free-proxy-discovery)"},
        ) as client:
            tasks = [self._fetch_one(client, n, u, p) for (n, u, p) in self.sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        seen: Set[Tuple[str, str, int]] = set()
        out: List[RawProxy] = []
        total_lines = 0
        for res in results:
            if isinstance(res, Exception):
                continue
            for rp in res:  # type: ignore[assignment]
                total_lines += 1
                key = (rp.protocol, rp.host, rp.port)
                if key in seen:
                    continue
                seen.add(key)
                out.append(rp)

        logger.info(
            f"[FreeProxyProvider] aggregated {len(out)} unique proxies "
            f"from {total_lines} lines across {len(self.sources)} sources"
        )
        return out

    async def _fetch_one(
        self,
        client: httpx.AsyncClient,
        name: str,
        url: str,
        protocol: str,
    ) -> List[RawProxy]:
        async with self._sem:
            try:
                resp = await client.get(url)
            except httpx.HTTPError as e:
                logger.warning(f"[FreeProxyProvider] {name}: fetch failed ({e.__class__.__name__})")
                return []

            if resp.status_code != 200 or not resp.text:
                logger.warning(f"[FreeProxyProvider] {name}: HTTP {resp.status_code}")
                return []

            parsed = list(self._parse(resp.text, protocol, name))
            logger.info(f"[FreeProxyProvider] {name}: parsed {len(parsed)} entries")
            return parsed

    @staticmethod
    def _parse(body: str, default_protocol: str, source: str) -> Iterable[RawProxy]:
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            m = _ADDR_RE.match(line)
            if not m:
                continue
            proto = (m.group(1) or default_protocol).lower()
            host = m.group(2)
            try:
                port = int(m.group(3))
            except ValueError:
                continue
            if not (1 <= port <= 65535):
                continue
            if proto not in ("http", "https", "socks4", "socks5"):
                continue
            yield RawProxy(protocol=proto, host=host, port=port, source=source)


async def discover_free_proxies(
    limit: Optional[int] = None,
    protocols: Optional[Iterable[str]] = None,
) -> List[RawProxy]:
    """Convenience helper — fetch, optionally filter by protocol, truncate."""
    provider = FreeProxyProvider()
    proxies = await provider.fetch_all()
    if protocols is not None:
        allowed = {p.lower() for p in protocols}
        proxies = [p for p in proxies if p.protocol in allowed]
    if limit is not None:
        proxies = proxies[:limit]
    return proxies
