"""REMAX.pt spider — JSON-LD primary, DOM fallback."""
from __future__ import annotations

from typing import Dict, List

from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver
from realestate_engine.scraping.spiders._extraction_mixin import ExtractionMixin


class REMAXSpider(ExtractionMixin, BaseSpiderNodriver):
    """Spider for remax.pt — real DOM + schema.org extraction."""

    name = "remax"
    DEFAULT_REGION = "porto"
    REGION_URLS = {
        "porto": "https://www.remax.pt/comprar/apartamento/porto",
        "lisboa": "https://www.remax.pt/comprar/apartamento/lisboa",
        "braga": "https://www.remax.pt/comprar/apartamento/braga",
        "coimbra": "https://www.remax.pt/comprar/apartamento/coimbra",
        "faro": "https://www.remax.pt/comprar/apartamento/faro",
        "setubal": "https://www.remax.pt/comprar/apartamento/setubal",
        "aveiro": "https://www.remax.pt/comprar/apartamento/aveiro",
        "leiria": "https://www.remax.pt/comprar/apartamento/leiria",
    }
    base_url = REGION_URLS[DEFAULT_REGION]
    sleep_range = (4, 9)

    def __init__(self, proxy_manager=None, region=None):
        super().__init__(proxy_manager)
        self.region = region or self.DEFAULT_REGION
        self.base_url = self.REGION_URLS.get(self.region, self.REGION_URLS[self.DEFAULT_REGION])

    # Ordered from most specific to most generic
    CARD_SELECTORS = [
        "[data-testid='card-property']",
        "article.property-card",
        "div.property-card",
        ".property-item",
        "[class*='PropertyCard']",
        "a[href*='/imovel/']",
    ]

    async def parse_page(self, page_num: int) -> List[Dict]:
        await self.accept_cookies()
        await self.scroll_page(6)

        listings: List[Dict] = []

        # Layer 1: JSON-LD — REMAX embeds Product/Offer schema for SEO
        entities = await self.extract_jsonld()
        for ent in entities:
            t = ent.get("@type")
            if t in ("Product", "Residence", "Apartment", "SingleFamilyResidence",
                     "RealEstateListing", "Offer"):
                url = ent.get("url") or (ent.get("offers") or {}).get("url") or ""
                offer = ent.get("offers") or {}
                price_text = str(offer.get("price") or ent.get("price") or "")
                if price_text and "€" not in price_text:
                    price_text = f"{price_text} €"
                image = ent.get("image") or []
                if isinstance(image, str):
                    image = [image]
                data = {
                    "source_id": self.derive_source_id(url) or ent.get("sku", ""),
                    "url": url,
                    "title": ent.get("name", "") or ent.get("description", "")[:120],
                    "description": ent.get("description", ""),
                    "price_text": price_text,
                    "area_text": self.extract_area_text(ent.get("description", "")),
                    "rooms_text": self.extract_rooms_text(ent.get("name", "")
                                                         + " "
                                                         + ent.get("description", "")),
                    "location": (ent.get("address", {}) or {}).get("addressLocality", ""),
                    "photos": image,
                    "portal": self.name,
                }
                if url:
                    listings.append(self.to_raw_listing(data))

        if listings:
            logger.info(f"[{self.name}] JSON-LD produced {len(listings)} listings on page {page_num}")
            return listings

        # Layer 2: DOM fallback across multiple possible card selectors
        for selector in self.CARD_SELECTORS:
            script = f"""
            (() => {{
                const out = [];
                document.querySelectorAll({selector!r}).forEach(el => {{
                    const a = el.querySelector('a[href*=\"/imovel/\"]') || (el.tagName === 'A' ? el : null);
                    if (!a) return;
                    const priceEl = el.querySelector('[class*=\"price\" i], [data-testid*=\"price\" i]');
                    const titleEl = el.querySelector('[class*=\"title\" i], h2, h3');
                    const locEl = el.querySelector('[class*=\"location\" i], [class*=\"address\" i]');
                    const imgEl = el.querySelector('img');
                    const full = el.innerText || '';
                    out.push({{
                        url: a.href || '',
                        title: titleEl ? titleEl.innerText.trim() : (a.innerText || '').trim(),
                        price_text: priceEl ? priceEl.innerText.trim() : '',
                        location: locEl ? locEl.innerText.trim() : '',
                        image: imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '',
                        full_text: full,
                    }});
                }});
                return out;
            }})()
            """
            results = await self.safe_evaluate(script, timeout=15.0)
            if results:
                logger.info(f"[{self.name}] selector={selector!r} produced {len(results)} listings")
                for r in results:
                    url = r.get("url", "")
                    if not url:
                        continue
                    listings.append(self.to_raw_listing({
                        "source_id": self.derive_source_id(url),
                        "url": url,
                        "title": r.get("title", ""),
                        "price_text": r.get("price_text", "") or self.extract_price_text(r.get("full_text", "")),
                        "area_text": self.extract_area_text(r.get("full_text", "")),
                        "rooms_text": self.extract_rooms_text((r.get("title", "") + " " + r.get("full_text", ""))),
                        "location": r.get("location", ""),
                        "photos": [r["image"]] if r.get("image") else [],
                        "portal": self.name,
                    }))
                break

        if not listings:
            logger.warning(f"[{self.name}] no listings extracted on page {page_num}")
            await self.take_debug_snapshot()

        logger.info(f"[{self.name}] Parsed {len(listings)} listings on page {page_num}")
        return listings

    async def get_next_page(self) -> bool:
        try:
            clicked = await self.safe_evaluate(
                "(() => { const el = document.querySelector("
                "'a[rel=\"next\"], a[aria-label*=\"next\" i], a[class*=\"next\" i]:not([disabled])'"
                "); if (el) { el.click(); return true; } return false; })()",
                timeout=5.0,
            )
            if clicked:
                import asyncio
                await asyncio.sleep(3)
                return True
        except Exception as e:
            logger.debug(f"[{self.name}] next-button click failed: {e}")
        # URL-based fallback
        try:
            import re
            url = await self.tab.evaluate("window.location.href")
            if "?" in url and re.search(r"[?&]page=\d+", url):
                new_url = re.sub(r"([?&]page=)(\d+)",
                                 lambda m: f"{m.group(1)}{int(m.group(2)) + 1}", url)
            else:
                new_url = url + ("&" if "?" in url else "?") + "page=2"
            await self.tab.get(new_url)
            return True
        except Exception:
            return False
