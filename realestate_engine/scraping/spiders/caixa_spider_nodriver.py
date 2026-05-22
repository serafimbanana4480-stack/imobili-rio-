"""Caixa Spider - Bank-owned properties (desinvestimento bancário).

Caixa Geral de Depósitos lists repossessed properties through
its real estate division, often at competitive prices.
"""
import asyncio
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver

UTC = timezone.utc


class CaixaSpider(BaseSpiderNodriver):
    """Spider for Caixa Geral de Depósitos bank-owned properties."""

    name = "caixa"
    base_url = "https://www.cgd.pt/Particulares/Casa/Casas-a-Venda/Pages/Casas-a-Venda.aspx"
    sleep_range = (5, 12)
    max_pages = 5

    async def parse_page(self, page_num: int) -> List[Dict]:
        listings = []

        try:
            await self.tab.get(self.base_url)
            await asyncio.sleep(4)

            await self.scroll_page(scroll_count=3)

            count = await self.wait_for_selector("div.property-item, div.imovel, article.card, div.listing-card", timeout=15.0)
            if count == 0:
                logger.warning(f"[{self.name}] No property items found on page {page_num}")
                return listings

            cards = await self.tab.query_selector_all("div.property-item, div.imovel, article.card, div.listing-card")

            for card in cards:
                try:
                    data = await self._extract_card(card)
                    if data and data.get("preco_pedido", 0) > 0:
                        listings.append(self.to_raw_listing(data))
                        self.stats["scraped"] += 1
                except Exception as e:
                    logger.warning(f"[{self.name}] Card extraction error: {e}")
                    continue

        except Exception as e:
            logger.error(f"[{self.name}] Page {page_num} parse error: {e}")

        return listings

    async def _extract_card(self, card) -> Optional[Dict]:
        try:
            title_el = await card.query_selector("h2, h3, .title, .property-title, .card-title")
            title = await title_el.text_content() if title_el else ""

            price_el = await card.query_selector(".price, .property-price, .card-price, span[class*='price'], span[class*='preco']")
            price_text = await price_el.text_content() if price_el else ""
            price = self._parse_price(price_text)

            area_el = await card.query_selector(".area, .property-area, .card-area, span[class*='area']")
            area_text = await area_el.text_content() if area_el else ""
            area = self._parse_area(area_text)

            location_el = await card.query_selector(".location, .property-location, .card-location, span[class*='local']")
            location = await location_el.text_content() if location_el else ""

            link_el = await card.query_selector("a[href]")
            url = await link_el.get_attribute("href") if link_el else ""
            if url and not url.startswith("http"):
                url = f"https://www.cgd.pt{url}" if url.startswith("/") else f"https://www.cgd.pt/{url}"

            rooms_el = await card.query_selector(".rooms, .property-rooms, .card-rooms, span[class*='quartos'], span[class*='rooms']")
            rooms_text = await rooms_el.text_content() if rooms_el else ""
            rooms = self._parse_int(rooms_text)

            source_id = url.split("/")[-1] if url else str(hash(title + location))[:12]

            return {
                "source_id": source_id,
                "url": url,
                "titulo": title.strip(),
                "preco_pedido": price,
                "area_util_m2": area,
                "quartos": rooms,
                "morada_raw": location.strip(),
                "scrape_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Card extraction failed: {e}")
            return None

    async def get_next_page(self) -> bool:
        try:
            next_btn = await self.tab.query_selector("a.next, a[rel='next'], button.next, .pagination-next, a.pagination__next")
            if next_btn:
                await next_btn.click()
                await asyncio.sleep(3)
                return True
        except Exception:
            pass
        return False

    def _parse_price(self, text: str) -> float:
        if not text:
            return 0.0
        text = re.sub(r"[^\d,.]", "", text)
        text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _parse_area(self, text: str) -> float:
        if not text:
            return 0.0
        nums = re.findall(r"[\d,.]+", text)
        if nums:
            return self._parse_price(nums[0])
        return 0.0

    def _parse_int(self, text: str) -> int:
        if not text:
            return 0
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else 0
