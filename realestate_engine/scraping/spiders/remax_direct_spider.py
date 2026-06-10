"""REMAX.pt direct-fetch spider — sitemap discovery + per-listing JSON-LD.

REMAX renders listing cards client-side (their ``__NEXT_DATA__`` only
carries filter/SEO config, not listings), but **every individual listing
detail page** ships a complete ``schema.org/Product`` block with:

    - offers.price (numeric EUR)
    - itemOffered.floorSize.value (m², ``unitCode=MTK``)
    - itemOffered.numberOfBedrooms
    - itemOffered.numberOfBathroomsTotal
    - itemOffered.address (street, locality, region)
    - description + image

Listing URLs live in public sitemaps
(``https://remax.pt/sitemap/listings_details_pt_1..4.xml.gz``), so we
discover them without a browser, filter by region/type, and fetch each
detail page concurrently (bounded, with pacing).

Matches the ``BaseSpiderNodriver.run`` contract:
    run(max_pages, headless) → List[raw_listing_dict]

``max_pages`` is reinterpreted here as "number of detail pages to
fetch", in batches of ``DETAIL_BATCH`` = 15. So ``max_pages=3`` → 45
listings scraped.
"""
from __future__ import annotations

import asyncio
import gzip
import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import httpx
from loguru import logger

from realestate_engine.scraping.http_client import default_headers, pick_user_agent
from realestate_engine.scraping.proxy_manager import ProxyManager


SITEMAP_ROOT = "https://remax.pt/sitemap/"
DETAIL_SITEMAPS_PT = [
    f"{SITEMAP_ROOT}listings_details_pt_{i}.xml.gz" for i in (1, 2, 3, 4)
]

LD_JSON_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")


def _walk_nodes(data: Any) -> Iterable[Dict]:
    """Flatten nested JSON-LD graphs into individual node dicts."""
    if isinstance(data, dict):
        yield data
        for key in ("@graph", "itemListElement", "mainEntity"):
            nested = data.get(key)
            if nested:
                yield from _walk_nodes(nested)
    elif isinstance(data, list):
        for item in data:
            yield from _walk_nodes(item)


def _extract_additional_property(product: Dict[str, Any], name_keywords: list) -> Optional[str]:
    """Extract a PropertyValue from schema.org Product additionalProperty by keyword match."""
    props = product.get("additionalProperty") or product.get("additionalProperties") or []
    if isinstance(props, dict):
        props = [props]
    if not isinstance(props, list):
        return None
    for p in props:
        if not isinstance(p, dict):
            continue
        prop_name = (p.get("name") or "").lower()
        if any(kw.lower() in prop_name for kw in name_keywords):
            val = p.get("value") or p.get("valueReference") or ""
            return str(val).strip() if val else None
    return None


class REMAXDirectSpider:
    """Direct-fetch REMAX spider: sitemap → detail → JSON-LD."""

    name = "remax"
    # Keyword in URL used to filter by region. Matches URLs like
    # ``/pt/imoveis/venda-apartamento-t2-porto-cedofeita/120141071-449``.
    REGION_KEYWORDS = (
        "porto", "lisboa", "braga", "coimbra", "faro", "setubal", "aveiro", "leiria",
        "vila-nova-de-gaia", "matosinhos", "maia", "gondomar", "valongo",
        "sintra", "cascais", "oeiras", "amadora", "seixal", "loures", "odivelas",
    )
    DETAIL_BATCH = 15       # listings fetched per "page" unit
    DETAIL_CONCURRENCY = 4  # simultaneous detail fetches
    request_delay = (0.4, 1.1)

    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.results: List[Dict[str, Any]] = []
        self.stats = {"sitemap_urls": 0, "candidates": 0, "parsed": 0, "errors": 0, "skipped": 0}

    async def run(self, max_pages: Optional[int] = None, headless: bool = True) -> List[Dict[str, Any]]:
        target_batches = max_pages or 3
        want_total = target_batches * self.DETAIL_BATCH
        logger.info(
            f"[{self.name}] starting sitemap-based run "
            f"(target={want_total} listings across {target_batches} batches)"
        )

        headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
        timeout = httpx.Timeout(45.0, connect=15.0)

        async with httpx.AsyncClient(
            headers=headers, timeout=timeout, follow_redirects=True, http2=False,
        ) as client:
            candidates = await self._discover_listing_urls(client, want_total * 3)
            if not candidates:
                logger.warning(f"[{self.name}] no sitemap URLs matched region filter")
                return []

            logger.info(
                f"[{self.name}] {len(candidates)} candidate URLs "
                f"(sitemap_urls={self.stats['sitemap_urls']})"
            )

            # Random sample so repeated runs pick up different listings
            random.shuffle(candidates)
            to_fetch = candidates[:want_total]

            sem = asyncio.Semaphore(self.DETAIL_CONCURRENCY)

            async def _one(url: str) -> None:
                async with sem:
                    record = await self._fetch_detail(client, url)
                    if record is not None:
                        self.results.append(record)
                    # pacing to avoid tripping rate limits
                    await asyncio.sleep(random.uniform(*self.request_delay))

            await asyncio.gather(*(_one(u) for u in to_fetch))

        logger.info(
            f"[{self.name}] run complete: parsed={len(self.results)} "
            f"(candidates={self.stats['candidates']}, errors={self.stats['errors']}, "
            f"skipped={self.stats['skipped']})"
        )
        return self.results

    # ------------------------------------------------------------------ #
    async def _discover_listing_urls(
        self,
        client: httpx.AsyncClient,
        hard_cap: int,
    ) -> List[str]:
        """Fetch + concatenate sitemaps until we have enough candidate URLs."""
        out: List[str] = []
        for sm_url in DETAIL_SITEMAPS_PT:
            try:
                r = await client.get(sm_url)
            except httpx.HTTPError as e:
                logger.warning(f"[{self.name}] sitemap {sm_url}: {e.__class__.__name__}")
                continue
            if r.status_code != 200:
                logger.warning(f"[{self.name}] sitemap {sm_url}: HTTP {r.status_code}")
                continue
            try:
                xml = gzip.decompress(r.content).decode("utf-8", errors="replace")
            except Exception:
                xml = r.text
            urls = LOC_RE.findall(xml)
            self.stats["sitemap_urls"] += len(urls)
            # Keep only slug-carrying URLs (filter out bare /pt/{id} shortlinks
            # that server-side redirect but don't include a readable slug),
            # and require the region keyword.
            for u in urls:
                low = u.lower()
                if "/imoveis/" not in low:
                    continue
                if not any(kw in low for kw in self.REGION_KEYWORDS):
                    continue
                # Apartment / house focus; skip land/commercial to keep ETL happy
                if not any(t in low for t in (
                    "venda-apartamento", "venda-moradia", "venda-quinta", "venda-duplex",
                )):
                    continue
                out.append(u)
            self.stats["candidates"] = len(out)
            if len(out) >= hard_cap:
                break
        return out

    async def _fetch_detail(self, client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
        last_error = None
        for attempt in range(1, 4):
            try:
                resp = await client.get(url, headers={"User-Agent": pick_user_agent()})
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}"
                    await asyncio.sleep(2 ** attempt)
                    continue
                body = resp.text
                # Extract JSON-LD Product
                product: Optional[Dict[str, Any]] = None
                for block in LD_JSON_RE.findall(body):
                    try:
                        data = json.loads(block.strip())
                    except json.JSONDecodeError:
                        continue
                    for node in _walk_nodes(data):
                        if node.get("@type") == "Product":
                            product = node
                            break
                    if product:
                        break
                if product is None:
                    self.stats["skipped"] += 1
                    return None
                return self._project(product, url)
            except httpx.HTTPError as e:
                last_error = f"{e.__class__.__name__}: {e}"
                await asyncio.sleep(2 ** attempt)
                continue
        logger.error(f"[{self.name}] detail {url}: failed after 3 attempts: {last_error}")
        self.stats["errors"] += 1
        return None

    def _project(self, product: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
        offers = product.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        item = offers.get("itemOffered") or {}

        # Price — must be numeric
        price = offers.get("price")
        try:
            price_value = int(float(price)) if price is not None else None
        except (TypeError, ValueError):
            price_value = None
        
        if price_value is None or price_value <= 0:
            logger.warning(f"[{self.name}] Skipped {url}: Invalid price {price}")
            self.stats["skipped"] += 1
            return None

        # Area from floorSize.value (m²)
        floor = item.get("floorSize") or {}
        area_val = floor.get("value") if isinstance(floor, dict) else None
        try:
            area = float(area_val) if area_val is not None else None
        except (TypeError, ValueError):
            area = None

        rooms_raw = item.get("numberOfBedrooms")
        try:
            rooms = int(rooms_raw) if rooms_raw is not None else None
        except (TypeError, ValueError):
            rooms = None

        baths_raw = item.get("numberOfBathroomsTotal")
        try:
            baths = int(baths_raw) if baths_raw is not None else None
        except (TypeError, ValueError):
            baths = None

        if area is None or rooms is None or area <= 0 or rooms < 0:
            logger.warning(f"[{self.name}] Skipped {url}: Area={area}, Rooms={rooms}")
            self.stats["skipped"] += 1
            return None

        address = item.get("address") or {}
        if isinstance(address, list):
            address = address[0] if address else {}

        # Derive a stable source_id from the URL tail (e.g. "120141071-449")
        tail = url.rstrip("/").split("/")[-1]
        m = re.match(r"(\d{5,}(?:-\d+)?)", tail)
        source_id = m.group(1) if m else tail

        name = product.get("name") or tail
        description = product.get("description") or ""
        image = product.get("image")
        if isinstance(image, list):
            image = image[0] if image else ""

        # Extract additional properties from schema.org Product
        energy_cert = _extract_additional_property(product, ["certificado energético", "energético", "cert. energético", "cee", "energy"])
        build_year = _extract_additional_property(product, ["ano de construção", "ano construção", "construção", "ano", "year built"])
        condition = _extract_additional_property(product, ["estado", "condição", "conservação", "condition"])

        raw_data: Dict[str, Any] = {
            "title": name,
            "price_text": f"{price_value:,} €".replace(",", "."),
            "area_text": f"{int(area)} m²",
            "rooms_text": f"T{rooms}",
            "description": description[:2000],
            "location": address.get("addressLocality", ""),
            "freguesia": address.get("addressLocality", ""),
            "concelho": address.get("addressLocality", ""),
            "distrito": address.get("addressRegion", ""),
            "lat": None,   # REMAX JSON-LD does not include geo in the detail
            "lon": None,
            "preco_pedido": price_value,
            "area_util_m2": area,
            "quartos": rooms,
            "casas_banho": baths,
            "image_url": image or "",
            "street": address.get("streetAddress", ""),
            "portal": self.name,
            "energy_cert": energy_cert,
            "year_built": build_year,
            "condition": condition,
        }

        return {
            "source_portal": self.name,
            "source_id": source_id,
            "source_url": url,
            "scrape_timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_data": raw_data,
        }
