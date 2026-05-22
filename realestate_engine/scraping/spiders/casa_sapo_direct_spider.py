"""casa.sapo.pt direct-fetch spider — zero browser, pure httpx.

casa.sapo.pt embeds one ``<script type="application/ld+json">`` block per
listing with the full ``schema.org/Offer`` payload, including:

    - name (title)
    - description (HTML-escaped)
    - price       — always ``["123.456 €"]`` (list of one string)
    - availableAtOrFrom.address  — addressCountry / Locality / Region
    - availableAtOrFrom.geo      — GeoCoordinates (lat/lon!)
    - image
    - seller

This bypasses the nodriver spider entirely (which gets rate-limited
with 429s and has flaky selectors). Same output contract as
``ImovirtualNextDataSpider`` so ``SpiderManager`` can drive it unchanged.

The ``+`` character in the script ``type`` attribute is HTML-entity
encoded on casa.sapo.pt (``application/ld&#x2B;json``), so the regex
matches both encodings.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from realestate_engine.scraping.proxy_manager import ProxyManager
from realestate_engine.scraping.http_client import default_headers, pick_user_agent


# Regex matches both "application/ld+json" and "application/ld&#x2B;json".
LD_JSON_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
PRICE_RE = re.compile(r"([\d\s\.,]+)\s*€")
AREA_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*m[²2]", re.IGNORECASE)
ROOMS_RE = re.compile(r"\bT(\d+)\b|(\d+)\s*quartos?", re.IGNORECASE)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def _clean_desc(raw: str) -> str:
    if not raw:
        return ""
    txt = BR_RE.sub("\n", raw)
    txt = TAG_RE.sub("", txt)
    return txt.strip()


def _price_to_int(price_field: Any) -> Optional[int]:
    """Parse ``["596.000 €"]`` or ``"596.000 €"`` → 596000."""
    if price_field is None:
        return None
    if isinstance(price_field, list):
        price_field = price_field[0] if price_field else None
    if not price_field:
        return None
    m = PRICE_RE.search(str(price_field))
    if not m:
        return None
    digits = re.sub(r"[^\d]", "", m.group(1))
    return int(digits) if digits else None


def _extract_additional_property(offer: Dict[str, Any], name_keywords: list) -> Optional[str]:
    """Extract a PropertyValue from schema.org Offer additionalProperty by keyword match."""
    props = offer.get("additionalProperty") or offer.get("additionalProperties") or []
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


def _parse_listing_id_from_image(image_url: str) -> str:
    """Extract the numeric listing id from the CDN image URL.

    Image URLs look like:
        https://media.casasapo.pt/.../P29821484/Tphoto/ID...jpg
    We take the ``P\\d+`` chunk as the stable listing id.
    """
    if not image_url:
        return ""
    m = re.search(r"/P(\d{5,})/", image_url)
    if m:
        return m.group(1)
    # Fallback: last numeric chunk
    nums = re.findall(r"\d{6,}", image_url)
    return nums[-1] if nums else ""


class CasaSapoDirectSpider:
    """Direct-fetch spider for casa.sapo.pt using embedded JSON-LD."""

    name = "casa_sapo"
    SEARCH_URLS = [
        "https://casa.sapo.pt/comprar/apartamentos/porto/",
        "https://casa.sapo.pt/comprar/apartamentos/lisboa/",
        "https://casa.sapo.pt/comprar/apartamentos/braga/",
        "https://casa.sapo.pt/comprar/apartamentos/coimbra/",
        "https://casa.sapo.pt/comprar/apartamentos/faro/",
        "https://casa.sapo.pt/comprar/apartamentos/setubal/",
        "https://casa.sapo.pt/comprar/apartamentos/aveiro/",
        "https://casa.sapo.pt/comprar/apartamentos/leiria/",
    ]
    base_url = SEARCH_URLS[0]
    max_pages = 20
    request_delay = (2.5, 5.0)  # be polite — portal rate-limits aggressively

    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.results: List[Dict[str, Any]] = []
        self.stats = {"pages": 0, "items": 0, "errors": 0, "skipped": 0, "rate_limited": 0}

    async def run(self, max_pages: Optional[int] = None, headless: bool = True) -> List[Dict[str, Any]]:
        """Run with the same contract as BaseSpiderNodriver.run."""
        target_pages = max_pages or self.max_pages
        logger.info(
            f"[{self.name}] starting direct-fetch run "
            f"(max_pages={target_pages} per region, regions={len(self.SEARCH_URLS)})"
        )

        # casa_sapo strategy is "hybrid" — SmartHttpClient would add proxies on retry,
        # but casa_sapo mostly works directly; use a single resilient session here.
        timeout = httpx.Timeout(30.0, connect=15.0)
        limits = httpx.Limits(max_connections=3, max_keepalive_connections=3)
        headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")

        seen_ids: set[str] = set()

        async with httpx.AsyncClient(
            headers=headers, timeout=timeout, limits=limits,
            follow_redirects=True, http2=False,
        ) as client:
            for region_url in self.SEARCH_URLS:
                region_label = region_url.rstrip("/").rsplit("/", 1)[-1]
                logger.info(f"[{self.name}] scraping region: {region_label}")
                referer = region_url

                for page_num in range(1, target_pages + 1):
                    # casa.sapo.pt paginates via ?pn=N
                    url = region_url if page_num == 1 else f"{region_url}?pn={page_num}"
                    offers = await self._fetch_offers(client, url, page_num, referer=referer)
                    referer = url

                    if offers is None:
                        self.stats["errors"] += 1
                        # If repeatedly rate-limited, back off with extra pacing
                        if self.stats["rate_limited"] >= 2:
                            logger.warning(f"[{self.name}] backing off after repeated 429s")
                            await asyncio.sleep(15.0)
                            self.stats["rate_limited"] = 0
                        continue

                    parsed = 0
                    for offer in offers:
                        record = self._project(offer, region_label)
                        if record is None:
                            self.stats["skipped"] += 1
                            continue
                        sid = record["source_id"]
                        # Ensure sid is always a string (never list/dict)
                        if isinstance(sid, (list, dict)):
                            sid = str(sid) if isinstance(sid, dict) else sid[0] if sid else ""
                        if not sid or sid in seen_ids:
                            self.stats["skipped"] += 1
                            continue
                        seen_ids.add(sid)
                        self.results.append(record)
                        parsed += 1

                    self.stats["pages"] += 1
                    self.stats["items"] += parsed
                    logger.info(
                        f"[{self.name}] {region_label} page {page_num}: "
                        f"offers={len(offers)} parsed={parsed} total={len(self.results)}"
                    )

                    # Early stop: no more offers on this page
                    if not offers:
                        logger.info(f"[{self.name}] {region_label}: empty page, stopping region")
                        break

                    # Rotate UA on each page to blend in, pace politely
                    client.headers["User-Agent"] = pick_user_agent()
                    await asyncio.sleep(random.uniform(*self.request_delay))

        logger.info(
            f"[{self.name}] direct-fetch run complete: {len(self.results)} listings "
            f"(pages={self.stats['pages']}, errors={self.stats['errors']}, "
            f"skipped={self.stats['skipped']})"
        )
        return self.results

    # ------------------------------------------------------------------ #
    async def _fetch_offers(
        self, client: httpx.AsyncClient, url: str, page_num: int, referer: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        headers = {}
        if referer:
            headers["Referer"] = referer
        try:
            resp = await client.get(url, headers=headers)
        except httpx.HTTPError as e:
            logger.warning(f"[{self.name}] page {page_num}: {e.__class__.__name__}")
            return None

        if resp.status_code == 429:
            self.stats["rate_limited"] += 1
            logger.warning(f"[{self.name}] page {page_num}: HTTP 429 rate-limited")
            return None
        if resp.status_code != 200:
            logger.warning(f"[{self.name}] page {page_num}: HTTP {resp.status_code}")
            return None

        return list(self._iter_offers(resp.text))

    @staticmethod
    def _iter_offers(body: str):
        for block in LD_JSON_RE.findall(body):
            raw = block.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            # Handle list-of-objects as well as single objects
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if isinstance(node, dict) and node.get("@type") == "Offer":
                    yield node

    def _project(self, offer: Dict[str, Any], region_label: str) -> Optional[Dict[str, Any]]:
        """Map a schema.org Offer → raw-listing dict accepted by the ETL."""
        image_primary = offer.get("image") or ""
        if isinstance(image_primary, list):
            image_primary = image_primary[0] if image_primary else ""

        # Extract source_id from multiple possible fields
        source_id = ""
        # 1. Try @id (schema.org identifier)
        _id = offer.get("@id") or ""
        if _id:
            m = re.search(r"/(\d{5,})", str(_id))
            if m:
                source_id = m.group(1)
        # 2. Try url tail
        if not source_id:
            _url = offer.get("url") or ""
            if _url:
                m = re.search(r"/(\d{5,})/", str(_url))
                if m:
                    source_id = m.group(1)
        # 3. Try image URL (CDN path)
        if not source_id:
            source_id = _parse_listing_id_from_image(image_primary)
        if not source_id:
            return None

        name = offer.get("name") or ""
        description = _clean_desc(offer.get("description") or "")
        price_value = _price_to_int(offer.get("price"))
        if price_value is None:
            return None

        # Area from name or description
        area_m = AREA_RE.search(f"{name} {description}")
        area = float(area_m.group(1).replace(",", ".")) if area_m else None

        rooms_m = ROOMS_RE.search(f"{name} {description}")
        rooms: Optional[int] = None
        if rooms_m:
            rooms = int(rooms_m.group(1) or rooms_m.group(2))

        place = offer.get("availableAtOrFrom") or {}
        addr = place.get("address") or {}
        geo = place.get("geo") or {}
        lat = geo.get("latitude") if isinstance(geo, dict) else None
        lon = geo.get("longitude") if isinstance(geo, dict) else None

        # Require a minimum of fields so the ETL validator is happy.
        if price_value is None or area is None or rooms is None:
            return None

        # Extract source_url from multiple possible fields
        url = offer.get("url") or ""
        if not url and _id:
            url = str(_id)
        if not url:
            # casa.sapo.pt detail pages are /p{source_id}
            url = f"https://casa.sapo.pt/p{source_id}"

        # Extract additional properties (energy cert, year, condition) from schema.org
        energy_cert = _extract_additional_property(offer, ["certificado energético", "energético", "cert. energético", "cee"])
        build_year = _extract_additional_property(offer, ["ano de construção", "ano construção", "construção", "ano"])
        condition = _extract_additional_property(offer, ["estado", "condição", "conservação"])

        raw_data: Dict[str, Any] = {
            "title": name,
            "price_text": f"{price_value:,} €".replace(",", "."),
            "area_text": f"{int(area)} m²" if area else "",
            "rooms_text": f"T{rooms}" if rooms is not None else "",
            "description": description[:2000],
            "location": addr.get("addressLocality") or "",
            "freguesia": addr.get("addressRegion") or "",
            "concelho": addr.get("addressLocality") or "",
            "distrito": addr.get("addressLocality") or "",  # best-effort; ETL re-geocodes
            "lat": lat,
            "lon": lon,
            "preco_pedido": price_value,
            "area_util_m2": area,
            "quartos": rooms,
            "image_url": image_primary,
            "region_label": region_label,
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
