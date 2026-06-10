"""SuperCasa.pt spider."""
from __future__ import annotations

from typing import Dict, List

from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver
from realestate_engine.scraping.spiders._extraction_mixin import ExtractionMixin


class SuperCasaSpider(ExtractionMixin, BaseSpiderNodriver):
    """Spider for supercasa.pt."""

    name = "supercasa"
    DEFAULT_REGION = "porto"
    REGION_URLS = {
        "porto": "https://supercasa.pt/comprar-apartamentos/porto",
        "lisboa": "https://supercasa.pt/comprar-apartamentos/lisboa",
        "braga": "https://supercasa.pt/comprar-apartamentos/braga",
        "coimbra": "https://supercasa.pt/comprar-apartamentos/coimbra",
        "faro": "https://supercasa.pt/comprar-apartamentos/faro",
        "setubal": "https://supercasa.pt/comprar-apartamentos/setubal",
        "aveiro": "https://supercasa.pt/comprar-apartamentos/aveiro",
        "leiria": "https://supercasa.pt/comprar-apartamentos/leiria",
    }
    base_url = REGION_URLS[DEFAULT_REGION]
    sleep_range = (4, 9)

    def __init__(self, proxy_manager=None, region=None):
        super().__init__(proxy_manager)
        self.region = region or self.DEFAULT_REGION
        self.base_url = self.REGION_URLS.get(self.region, self.REGION_URLS[self.DEFAULT_REGION])

    CARD_SELECTORS = [
        "article.property",
        "div.property",
        "[class*='property-list-content'] article",
        "[class*='PropertyCard']",
        "a[href*='/comprar/']",
    ]

    async def parse_page(self, page_num: int) -> List[Dict]:
        await self.accept_cookies()
        await self.scroll_page(6)

        listings: List[Dict] = []

        # Try JSON-LD
        for ent in await self.extract_jsonld():
            t = ent.get("@type")
            if t in ("Product", "Residence", "Apartment", "RealEstateListing"):
                url = ent.get("url") or ""
                offer = ent.get("offers") or {}
                price_text = str(offer.get("price") or ent.get("price") or "")
                if price_text and "€" not in price_text:
                    price_text = f"{price_text} €"
                image = ent.get("image") or []
                if isinstance(image, str):
                    image = [image]
                if url:
                    listings.append(self.to_raw_listing({
                        "source_id": self.derive_source_id(url),
                        "url": url,
                        "title": ent.get("name", ""),
                        "description": ent.get("description", ""),
                        "price_text": price_text,
                        "area_text": self.extract_area_text(ent.get("description", "")),
                        "rooms_text": self.extract_rooms_text(
                            (ent.get("name", "") + " " + ent.get("description", ""))
                        ),
                        "location": (ent.get("address", {}) or {}).get("addressLocality", ""),
                        "photos": image,
                        "portal": self.name,
                    }))

        if listings:
            logger.info(f"[{self.name}] JSON-LD produced {len(listings)} listings on page {page_num}")
            return listings

        for selector in self.CARD_SELECTORS:
            script = f"""
            (() => {{
                const out = [];
                document.querySelectorAll({selector!r}).forEach(el => {{
                    const a = el.matches('a') ? el : el.querySelector('a[href*=\"/comprar/\"], a[href*=\"/imovel/\"]');
                    if (!a) return;
                    const priceEl = el.querySelector('[class*=\"price\" i]');
                    const titleEl = el.querySelector('h2, h3, [class*=\"title\" i]');
                    const locEl = el.querySelector('[class*=\"location\" i], [class*=\"address\" i]');
                    const imgEl = el.querySelector('img');
                    out.push({{
                        url: a.href || '',
                        title: titleEl ? titleEl.innerText.trim() : '',
                        price_text: priceEl ? priceEl.innerText.trim() : '',
                        location: locEl ? locEl.innerText.trim() : '',
                        image: imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '',
                        full_text: el.innerText || '',
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
                        "rooms_text": self.extract_rooms_text(
                            (r.get("title", "") + " " + r.get("full_text", ""))
                        ),
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
                "'a[rel=\"next\"], .pagination a.next, a[class*=\"next\" i]'"
                "); if (el) { el.click(); return true; } return false; })()",
                timeout=5.0,
            )
            if clicked:
                import asyncio
                await asyncio.sleep(3)
                return True
        except Exception:
            pass
        try:
            import re
            url = await self.tab.evaluate("window.location.href")
            if re.search(r"/p-\d+", url):
                new_url = re.sub(r"/p-(\d+)",
                                 lambda m: f"/p-{int(m.group(1)) + 1}", url)
            elif re.search(r"[?&]page=\d+", url):
                new_url = re.sub(r"([?&]page=)(\d+)",
                                 lambda m: f"{m.group(1)}{int(m.group(2)) + 1}", url)
            else:
                new_url = url.rstrip("/") + "/p-2"
            await self.tab.get(new_url)
            return True
        except Exception:
            return False
