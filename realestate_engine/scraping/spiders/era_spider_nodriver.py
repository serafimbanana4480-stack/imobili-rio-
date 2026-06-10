"""ERA spider using Nodriver."""
from typing import List, Dict
from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver


class ERASpider(BaseSpiderNodriver):
    """Spider for era.pt with multiple selector fallbacks."""
    
    name = "era"
    DEFAULT_REGION = "porto"
    REGION_URLS = {
        "porto": "https://www.era.pt/comprar/apartamentos/porto",
        "lisboa": "https://www.era.pt/comprar/apartamentos/lisboa",
        "braga": "https://www.era.pt/comprar/apartamentos/braga",
        "coimbra": "https://www.era.pt/comprar/apartamentos/coimbra",
        "faro": "https://www.era.pt/comprar/apartamentos/faro",
        "setubal": "https://www.era.pt/comprar/apartamentos/setubal",
        "aveiro": "https://www.era.pt/comprar/apartamentos/aveiro",
        "leiria": "https://www.era.pt/comprar/apartamentos/leiria",
    }
    base_url = REGION_URLS[DEFAULT_REGION]
    sleep_range = (3, 6)

    def __init__(self, proxy_manager=None, region=None):
        super().__init__(proxy_manager)
        self.region = region or self.DEFAULT_REGION
        self.base_url = self.REGION_URLS.get(self.region, self.REGION_URLS[self.DEFAULT_REGION])
    
    # Multiple selector fallbacks for robustness
    card_selectors = [
        '[class*="PropertyCard"]',
        '[class*="property-card"]',
        '[class*="ListingCard"]',
        '[class*="listing-card"]',
        '[class*="card"]',
        '.property-card',
        '[data-testid*="property"]',
        '.PropertyCard',
        '.listing-item',
        '.search-result-card',
        '[class*="result"]',
        '[class*="item"]',
    ]
    
    price_selectors = [
        '.price',
        '[data-testid*="price"]',
        '.property-price',
        '.listing-price',
    ]
    
    title_selectors = [
        '.title',
        '[data-testid*="title"]',
        '.property-title',
        'h2',
        'h3',
    ]
    
    link_selectors = [
        'a',
        '[data-testid*="link"]',
        '.property-link',
    ]
    
    def extract_area_from_text(self, text: str) -> str:
        """Extract area from text using multiple patterns."""
        import re
        if not text:
            return ''
        
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*m[²²]',
            r'(\d+(?:[.,]\d+)?)\s*m2',
            r'(\d+(?:[.,]\d+)?)\s*sqm',
            r'(\d+(?:[.,]\d+)?)\s*m',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return ''
    
    def extract_rooms_from_text(self, text: str) -> str:
        """Extract rooms from text using multiple patterns."""
        import re
        if not text:
            return ''
        
        patterns = [
            r'T(\d+)',
            r'(\d+)\s*quartos?',
            r'(\d+)\s*bedrooms?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return ''
    
    async def parse_page(self, page_num: int) -> List[Dict]:
        """Parse listings from ERA search page.

        era.pt renders its SearchList module client-side (``window.renderSearchList``).
        Generic ``[class*="card"]`` selectors match navbar/layout cards, so we use
        property-URL anchors (``/imovel/``) as the canonical signal and walk up
        to the enclosing card element to extract price/title/area.
        """
        # Wait for the SPA to hydrate and inject property anchors
        anchor_selector = 'a[href*="/imovel/"]'
        found = await self.wait_for_selector(anchor_selector, timeout=25.0)
        if not found:
            logger.warning(f"[{self.name}] Property anchors never appeared on page {page_num}")
            await self.take_debug_snapshot()
            return []

        # Allow lazy images / additional cards to stream in
        await self.scroll_page(scroll_count=4)
        await self.human_like_behavior()

        script = """
        (function() {
            const anchors = Array.from(document.querySelectorAll('a[href*="/imovel/"]'));
            const seen = new Set();
            const results = [];
            for (const a of anchors) {
                const href = a.href || '';
                if (!href || seen.has(href)) continue;
                seen.add(href);

                // Walk up to the nearest card-like container (max 6 levels)
                let card = a;
                for (let i = 0; i < 6 && card.parentElement; i++) {
                    card = card.parentElement;
                    const txt = card.innerText || '';
                    if (txt.includes('€') && txt.length > 40) break;
                }
                const text = (card.innerText || '').trim();

                const priceMatch = text.match(/([\\d][\\d\\s.]*\\s*€)/);
                const areaMatch = text.match(/(\\d+(?:[.,]\\d+)?)\\s*m[²2]/i);
                const roomsMatch = text.match(/T\\d+/i);
                const titleEl = card.querySelector('h1, h2, h3, h4, h5') || a;
                const title = (titleEl.innerText || '').trim().split('\\n')[0];

                const idMatch = href.match(/\\/imovel\\/(\\d+)/);
                results.push({
                    source_id: idMatch ? idMatch[1] : '',
                    url: href,
                    title: title,
                    price_text: priceMatch ? priceMatch[1].trim() : '',
                    area_text: areaMatch ? areaMatch[0] : '',
                    rooms_text: roomsMatch ? roomsMatch[0] : '',
                    full_text: text.slice(0, 400),
                });
            }
            return results;
        })()
        """
        raw_results = await self.safe_evaluate(script, timeout=20.0) or []
        logger.info(f"[{self.name}] Extracted {len(raw_results)} unique property anchors")

        listings = []
        for data in raw_results:
            if not data.get("price_text") and not data.get("title"):
                continue
            full_text = data.get("full_text", "")
            area = data.get("area_text") or self.extract_area_from_text(full_text)
            rooms = data.get("rooms_text") or self.extract_rooms_from_text(full_text)
            listings.append(self.to_raw_listing({
                "source_id": data.get("source_id", ""),
                "url": data.get("url", ""),
                "title": data.get("title", ""),
                "price_text": data.get("price_text", ""),
                "area_text": area,
                "rooms_text": rooms,
                "portal": self.name,
            }))

        if not listings:
            logger.warning(f"[{self.name}] Found anchors but no usable price/title fields")
            await self.take_debug_snapshot()

        logger.info(f"[{self.name}] Parsed {len(listings)} listings on page {page_num}")
        return listings

    async def get_next_page(self) -> bool:
        """Navigate to next page using URL increment."""
        try:
            url = await self.tab.evaluate("window.location.href")
            if '?page=' in url:
                import re
                new_url = re.sub(r'page=\d+', lambda m: f"page={int(m.group().split('=')[1])+1}", url)
                await self.tab.get(new_url)
            else:
                await self.tab.get(url + "?page=2")
            return True
        except Exception as e:
            logger.warning(f"[{self.name}] Could not navigate to next page: {e}")
            return False
    
    async def close_browser(self):
        """Close the browser."""
        if self.browser:
            try:
                self.browser.stop()
                logger.info(f"[{self.name}] Browser closed")
            except Exception as e:
                logger.warning(f"[{self.name}] Error closing browser: {e}")
