"""Imovirtual spider using Next.js ``__NEXT_DATA__`` JSON extraction.

Imovirtual renders every search page with a fully populated
``<script id="__NEXT_DATA__">`` payload containing the listings as
structured JSON. No browser automation is required, so this spider uses
``httpx`` with realistic desktop headers and paginates through the SSR
results directly. Drops the DOM-scraping / anti-bot overhead entirely.

Data path (verified 2026-04):
    props.pageProps.data.searchAds.items   -> list of ad dicts
    props.pageProps.data.searchAds.pagination.totalPages -> int

Each item exposes deterministic fields (``totalPrice``, ``areaInSquareMeters``,
``roomsNumber``, ``location.address``, ...), which the normalizer consumes
after we project them into the pipeline's canonical keys.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from realestate_engine.scraping.proxy_manager import ProxyManager


# Numeric word → digit (Imovirtual emits enums like "TWO", "THREE", etc.)
_ROOM_WORDS = {
    "ZERO": 0, "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4,
    "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
}


def _rooms_to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().upper()
    if text in _ROOM_WORDS:
        return _ROOM_WORDS[text]
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def _walk_search_ads(data: Any) -> Optional[Dict[str, Any]]:
    """Return the first ``searchAds`` dict found in the ``__NEXT_DATA__`` tree.

    Defensive: the exact path has been
    ``props.pageProps.data.searchAds`` for >2 years, but any subtree that
    exposes ``items`` + ``pagination`` will work.
    """
    if isinstance(data, dict):
        if (
            "searchAds" in data
            and isinstance(data["searchAds"], dict)
            and "items" in data["searchAds"]
        ):
            return data["searchAds"]
        for v in data.values():
            found = _walk_search_ads(v)
            if found is not None:
                return found
    elif isinstance(data, list):
        for v in data:
            found = _walk_search_ads(v)
            if found is not None:
                return found
    return None


class ImovirtualNextDataSpider:
    """Direct-fetch Imovirtual spider (no browser, no proxy needed).

    Implements the same contract as ``BaseSpiderNodriver.run`` so
    ``SpiderManager`` can drive it unchanged: returns a list of dicts with
    ``source_portal``, ``source_id``, ``source_url``, ``scrape_timestamp``,
    ``raw_data``.
    """

    name = "imovirtual"
    # Multiple search regions to maximise unique listing coverage
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
    base_url = SEARCH_URLS[0]  # kept for backwards compat
    max_pages = 20
    request_delay = (1.2, 2.8)  # jitter seconds between pages

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
    }

    NEXT_DATA_RE = re.compile(
        r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        re.DOTALL,
    )

    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.results: List[Dict[str, Any]] = []
        self.stats = {"pages": 0, "items": 0, "errors": 0, "skipped": 0}

    # --- public contract mirroring BaseSpiderNodriver.run -----------------
    async def run(self, max_pages: Optional[int] = None, headless: bool = True) -> List[Dict[str, Any]]:
        target_pages = max_pages or self.max_pages
        logger.info(f"[{self.name}] starting direct-fetch run (max_pages={target_pages} per region, regions={len(self.SEARCH_URLS)})")

        # Optional residential proxy — respected if configured, but not required.
        proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None

        timeout = httpx.Timeout(30.0, connect=15.0)
        limits = httpx.Limits(max_connections=4, max_keepalive_connections=4)

        client_kwargs: Dict[str, Any] = dict(
            headers=self.HEADERS,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            http2=False,
        )
        if proxy:
            client_kwargs["proxy"] = proxy

        seen_ids: set[str] = set()  # cross-region source_id dedup

        async with httpx.AsyncClient(**client_kwargs) as client:
            for region_url in self.SEARCH_URLS:
                region_label = region_url.rsplit("/", 1)[-1]
                logger.info(f"[{self.name}] scraping region: {region_label}")
                total_pages_hint: Optional[int] = None

                for page_num in range(1, target_pages + 1):
                    url = region_url if page_num == 1 else f"{region_url}?page={page_num}"
                    payload = await self._fetch_next_data(client, url, page_num)
                    if payload is None:
                        self.stats["errors"] += 1
                        continue

                    search_ads = _walk_search_ads(payload)
                    if not search_ads:
                        logger.warning(
                            f"[{self.name}] {region_label} page {page_num}: searchAds tree missing"
                        )
                        self.stats["errors"] += 1
                        continue

                    items = search_ads.get("items") or []
                    pagination = search_ads.get("pagination") or {}
                    if total_pages_hint is None:
                        total_pages_hint = pagination.get("totalPages")
                        if total_pages_hint:
                            logger.info(
                                f"[{self.name}] {region_label}: total results={pagination.get('totalItems')} "
                                f"pages={total_pages_hint}"
                            )

                    parsed = 0
                    for item in items:
                        record = self._project_item(item)
                        if record is None:
                            self.stats["skipped"] += 1
                            continue
                        sid = record["source_id"]
                        if sid in seen_ids:
                            continue
                        seen_ids.add(sid)
                        self.results.append(record)
                        parsed += 1

                    self.stats["pages"] += 1
                    self.stats["items"] += parsed
                    logger.info(
                        f"[{self.name}] {region_label} page {page_num}: parsed={parsed} "
                        f"running_total={len(self.results)}"
                    )

                    # Stop early if site says we're past the end
                    if total_pages_hint and page_num >= total_pages_hint:
                        break

                    # Pacing to stay polite
                    delay = random.uniform(*self.request_delay)
                    await asyncio.sleep(delay)

        logger.info(
            f"[{self.name}] direct-fetch run complete: "
            f"{len(self.results)} listings over {self.stats['pages']} pages "
            f"(errors={self.stats['errors']}, skipped={self.stats['skipped']})"
        )
        return self.results

    # --- internals --------------------------------------------------------
    async def _fetch_next_data(
        self,
        client: httpx.AsyncClient,
        url: str,
        page_num: int,
    ) -> Optional[Any]:
        last_error = None
        for attempt in range(1, 4):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}"
                    await asyncio.sleep(2 ** attempt)
                    continue
                match = self.NEXT_DATA_RE.search(resp.text)
                if not match:
                    logger.warning(f"[{self.name}] page {page_num}: __NEXT_DATA__ not found")
                    return None
                return json.loads(match.group(1))
            except asyncio.CancelledError:
                logger.warning(f"[{self.name}] page {page_num}: request cancelled (asyncio.CancelledError)")
                return None
            except httpx.HTTPError as e:
                last_error = f"{e.__class__.__name__}: {e}"
                await asyncio.sleep(2 ** attempt)
                continue
            except json.JSONDecodeError as e:
                logger.error(f"[{self.name}] page {page_num}: JSON parse error: {e}")
                return None
        logger.error(f"[{self.name}] page {page_num}: failed after 3 attempts: {last_error}")
        return None

    def _project_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Project an Imovirtual ad dict into the pipeline's raw-listing shape.

        Returns ``None`` if the item is missing the minimum fields required
        by the ETL (price + area); this filters promoted / banner cards that
        occasionally leak into the list.
        """
        ad_id = item.get("id")
        if not ad_id:
            return None

        price_block = item.get("totalPrice") or item.get("price") or {}
        price = price_block.get("value") if isinstance(price_block, dict) else price_block
        area = item.get("areaInSquareMeters")
        rooms = _rooms_to_int(item.get("roomsNumber"))
        bathrooms = _rooms_to_int(item.get("bathroomsNumber"))

        # Additional features: energy cert, build year, condition
        energy_cert = item.get("energyCertificate") or item.get("energy_cert") or item.get("energyLabel")
        build_year = item.get("buildYear") or item.get("yearBuilt") or item.get("constructionYear")
        condition = item.get("condition") or item.get("buildingCondition") or item.get("state")

        if price is None or area is None or rooms is None:
            return None

        location = item.get("location") or {}
        address = location.get("address") if isinstance(location, dict) else {}
        mapd = location.get("mapDetails") if isinstance(location, dict) else {}
        rg = location.get("reverseGeocoding") if isinstance(location, dict) else {}

        # Primary source: reverseGeocoding.locations carries hierarchical levels
        freguesia: Optional[str] = None
        concelho: Optional[str] = None
        distrito: Optional[str] = None
        if isinstance(rg, dict):
            for lvl in rg.get("locations") or []:
                if not isinstance(lvl, dict):
                    continue
                level = (lvl.get("locationLevel") or "").lower()
                name = lvl.get("name")
                if not name:
                    continue
                if level == "parish" and not freguesia:
                    freguesia = name
                elif level == "council" and not concelho:
                    concelho = name
                elif level == "district" and not distrito:
                    distrito = name

        # Secondary source: address.{city,province}.name
        if isinstance(address, dict):
            if not freguesia:
                city = address.get("city")
                if isinstance(city, dict):
                    freguesia = city.get("name")
            if not distrito:
                prov = address.get("province")
                if isinstance(prov, dict):
                    distrito = prov.get("name")

        street_name = None
        if isinstance(address, dict):
            street = address.get("street")
            if isinstance(street, dict):
                street_name = street.get("name")

        # mapDetails.coordinates may be absent (privacy) — leave geocoder to fill
        lat = None
        lon = None
        if isinstance(mapd, dict):
            coords = mapd.get("location") or mapd.get("coordinates") or {}
            if isinstance(coords, dict):
                lat = coords.get("latitude") or coords.get("lat")
                lon = coords.get("longitude") or coords.get("lng") or coords.get("lon")

        address_parts = [p for p in (street_name, freguesia, concelho, distrito) if p]
        morada_raw = ", ".join(address_parts)

        slug = item.get("slug") or ""
        detail_url = (
            f"https://www.imovirtual.com/pt/anuncio/{slug}"
            if slug
            else f"https://www.imovirtual.com/pt/anuncio/{ad_id}"
        )

        images = item.get("images") or []
        photo_urls: List[str] = []
        if isinstance(images, list):
            for img in images:
                if isinstance(img, dict):
                    url = img.get("large") or img.get("medium") or img.get("small")
                    if url:
                        photo_urls.append(url)

        agency_block = item.get("agency") or {}
        agency_name = agency_block.get("name") if isinstance(agency_block, dict) else None

        raw_data = {
            "source_id": str(ad_id),
            "url": detail_url,
            "title": item.get("title") or "",
            "description": item.get("shortDescription") or item.get("description") or "",
            "price": price,
            "preco": price,
            "price_text": f"{price} €",
            "area": area,
            "area_text": f"{area} m²",
            "rooms": rooms,
            "rooms_text": f"T{rooms}",
            "bathrooms": bathrooms,
            "photos": photo_urls,
            "fotos": photo_urls,
            "agency": agency_name or "",
            "agencia": agency_name or "",
            "location": morada_raw,
            "morada": morada_raw,
            "address": morada_raw,
            "morada_raw": morada_raw,
            "freguesia": freguesia or "",
            "concelho": concelho or "Porto",
            "distrito": distrito or "Porto",
            "lat": lat,
            "lon": lon,
            "portal": self.name,
            "energy_cert": energy_cert,
            "year_built": build_year,
            "condition": condition,
        }

        return {
            "id": str(uuid.uuid4()),
            "source_portal": self.name,
            "source_id": str(ad_id),
            "source_url": detail_url,
            "scrape_timestamp": datetime.now(UTC).isoformat(),
            "raw_data": raw_data,
        }
