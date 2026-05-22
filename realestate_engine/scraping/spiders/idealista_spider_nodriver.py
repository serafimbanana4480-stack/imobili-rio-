"""Idealista spider using Nodriver."""
from typing import List, Dict
from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver
from realestate_engine.scraping.spiders.extraction_mixin import ExtractionMixin


class IdealistaSpider(ExtractionMixin, BaseSpiderNodriver):
    """Spider for idealista.pt with pagination and cookie consent handling."""
    
    name = "idealista"
    base_url = "https://www.idealista.pt/venda-habitacoes/porto-districto/com-fotos/?ordem=atualizado-desc"
    
    # Multiple selector fallbacks for robustness
    card_selectors = [
        'article.item',
        '[data-testid*="listing"]',
        '.item-container',
        '.listing-card',
        '[class*="listing"]',
    ]
    
    link_selectors = [
        'a.item-link',
        'a[class*="item"]',
        'a',
    ]
    
    price_selectors = [
        '.item-price',
        '[data-testid*="price"]',
        '[class*="price"]',
    ]
    
    detail_selectors = [
        '.item-detail',
        '[class*="detail"]',
        'span',
    ]
    
    async def accept_cookies(self):
        """Handle cookie consent banner if present."""
        try:
            # Try common cookie consent button selectors
            cookie_selectors = [
                '#didomi-notice-agree-button',
                '[class*="cookie"] button',
                '[id*="cookie"] button',
                'button[class*="accept"]',
                'button[class*="agree"]',
            ]
            
            for selector in cookie_selectors:
                result = await self.safe_evaluate(
                    f"document.querySelector('{selector}') ? document.querySelector('{selector}').click() : null",
                    timeout=3.0
                )
                if result:
                    logger.info(f"[{self.name}] Clicked cookie consent button: {selector}")
                    await self.smart_sleep(1, 2)
                    break
        except Exception as e:
            logger.debug(f"[{self.name}] Cookie consent handling: {e}")
    
    async def extract_json_ld(self) -> List[Dict]:
        """Extract listings from JSON-LD schema.org data."""
        script = """
        Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
            .map(s => JSON.parse(s.innerText))
            .filter(j => j['@type'] === 'ItemList' || j['mainEntityOfPage'])
            .map(j => j.itemListElement || j.mainEntity)
            .flat()
            .filter(i => i)
        """
        return await self.safe_evaluate(script) or []

    async def parse_page(self, page_num: int) -> List[Dict]:
        """Parse listings with JSON-LD primary and DOM fallback."""
        await self.accept_cookies()
        
        # Layer 1: JSON-LD
        json_results = await self.extract_json_ld()
        if json_results:
            logger.info(f"[{self.name}] Found {len(json_results)} items via JSON-LD")
            # Convert JSON-LD to our format (simplified)
            # ... 
            
        # Layer 2: DOM Fallback (Existing logic)
        listings = []
        
        # Try each card selector until we find results
        for card_selector in self.card_selectors:
            script = f"""
            Array.from(document.querySelectorAll('{card_selector}')).map(el => {{
                const link = el.querySelector('a');
                const price = el.querySelector('.item-price') || el.querySelector('[class*="price"]');
                const details = Array.from(el.querySelectorAll('.item-detail, span')).map(d => d.innerText.trim());
                return {{
                    source_id: el.getAttribute('data-adid') || (link ? link.href.split('/').pop() : ''),
                    url: link ? link.href : '',
                    title: link ? link.innerText.trim() : '',
                    price_text: price ? price.innerText.trim() : '',
                    details: details,
                }};
            }});
            """
            results = await self.safe_evaluate(script, timeout=15.0)
            
            if results and len(results) > 0:
                logger.info(f"[{self.name}] Found {len(results)} listings using selector: {card_selector}")
                
                for data in results:
                    # Parse area and rooms using robust mixin methods
                    full_text = " ".join(data.get('details', [])) + " " + data.get('title', '')
                    area = self.extract_area_text(full_text)
                    rooms = self.extract_rooms_text(full_text)
                    
                    raw = self.to_raw_listing({
                        **data,
                        "area_text": area,
                        "rooms_text": rooms,
                        "portal": self.name
                    })
                    listings.append(raw)
                break
            else:
                logger.debug(f"[{self.name}] No results with selector: {card_selector}")
        
        if not listings:
            logger.warning(f"[{self.name}] No listings found with any selector")
            await self.take_debug_snapshot()
        
        logger.info(f"[{self.name}] Parsed {len(listings)} listings on page {page_num}")
        return listings

    async def get_next_page(self) -> bool:
        """Click next page button."""
        try:
            next_btn = await self.tab.find('.next > a')
            if next_btn:
                await next_btn.click()
                return True
        except:
            pass
        return False
    
    async def close_browser(self):
        """Close the browser."""
        if self.browser:
            try:
                self.browser.stop()
                logger.info(f"[{self.name}] Browser closed")
            except Exception as e:
                logger.warning(f"[{self.name}] Error closing browser: {e}")
