"""OLX.pt spider — DOM based (OLX list cards do not expose full JSON-LD)."""
from __future__ import annotations

from typing import Dict, List

from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver
from realestate_engine.scraping.spiders._extraction_mixin import ExtractionMixin


class OLXSpider(ExtractionMixin, BaseSpiderNodriver):
    """Spider for olx.pt list pages."""

    name = "olx"
    DEFAULT_REGION = "porto"
    REGION_URLS = {
        "porto": "https://www.olx.pt/imoveis/apartamentos/porto/",
        "lisboa": "https://www.olx.pt/imoveis/apartamentos/lisboa/",
        "braga": "https://www.olx.pt/imoveis/apartamentos/braga/",
        "coimbra": "https://www.olx.pt/imoveis/apartamentos/coimbra/",
        "faro": "https://www.olx.pt/imoveis/apartamentos/faro/",
        "setubal": "https://www.olx.pt/imoveis/apartamentos/setubal/",
        "aveiro": "https://www.olx.pt/imoveis/apartamentos/aveiro/",
        "leiria": "https://www.olx.pt/imoveis/apartamentos/leiria/",
    }
    base_url = REGION_URLS[DEFAULT_REGION]
    sleep_range = (4, 9)

    def __init__(self, proxy_manager=None, region=None):
        super().__init__(proxy_manager)
        self.region = region or self.DEFAULT_REGION
        self.base_url = self.REGION_URLS.get(self.region, self.REGION_URLS[self.DEFAULT_REGION])

    CARD_SELECTORS = [
        "div[data-cy='l-card']",
        "div[data-testid='l-card']",
        "a[data-cy='l-card']",
        "div[class*='css-'] a[href*='/d/anuncio/']",
    ]

    async def parse_page(self, page_num: int) -> List[Dict]:
        await self.accept_cookies()
        await self.scroll_page(6)

        listings: List[Dict] = []
        for selector in self.CARD_SELECTORS:
            script = f"""
            (() => {{
                const out = [];
                document.querySelectorAll({selector!r}).forEach(el => {{
                    const a = el.matches('a') ? el : el.querySelector('a[href*=\"/d/anuncio/\"]');
                    if (!a) return;
                    const priceEl = el.querySelector('[data-testid=\"ad-price\"], p.css-13afqrm, [class*=\"price\" i]');
                    const titleEl = el.querySelector('h4, h6, [class*=\"title\" i]');
                    const locEl = el.querySelector('[data-testid=\"location-date\"], p.css-1a4brun, [class*=\"location\" i]');
                    const imgEl = el.querySelector('img');
                    out.push({{
                        url: a.href || '',
                        title: titleEl ? titleEl.innerText.trim() : (a.getAttribute('aria-label') || a.innerText || '').trim(),
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
                        "price_text": r.get("price_text", ""),
                        "area_text": self.extract_area_text(
                            (r.get("title", "") + " " + r.get("full_text", ""))
                        ),
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
                "'a[data-cy=\"pagination-forward\"], a[data-testid=\"pagination-forward\"]'"
                "); if (el) { el.click(); return true; } return false; })()",
                timeout=5.0,
            )
            if clicked:
                import asyncio
                await asyncio.sleep(3)
                return True
        except Exception as e:
            logger.debug(f"[{self.name}] pagination-forward click failed: {e}")
        # URL fallback: OLX uses ?page=N
        try:
            import re
            url = await self.tab.evaluate("window.location.href")
            if re.search(r"[?&]page=\d+", url):
                new_url = re.sub(r"([?&]page=)(\d+)",
                                 lambda m: f"{m.group(1)}{int(m.group(2)) + 1}", url)
            else:
                new_url = url + ("&" if "?" in url else "?") + "page=2"
            await self.tab.get(new_url)
            return True
        except Exception:
            return False
