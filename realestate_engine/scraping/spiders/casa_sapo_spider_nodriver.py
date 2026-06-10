"""CasaSapo spider using Nodriver."""
from typing import List, Dict
from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver


class CasaSapoSpider(BaseSpiderNodriver):
    """Spider for casasapo.pt with scroll timeout protection and selector fallbacks."""
    
    name = "casasapo"
    DEFAULT_REGION = "porto"
    REGION_URLS = {
        "porto": "https://casasapo.pt/venda-apartamentos/porto/",
        "lisboa": "https://casasapo.pt/venda-apartamentos/lisboa/",
        "braga": "https://casasapo.pt/venda-apartamentos/braga/",
        "coimbra": "https://casasapo.pt/venda-apartamentos/coimbra/",
        "faro": "https://casasapo.pt/venda-apartamentos/faro/",
        "setubal": "https://casasapo.pt/venda-apartamentos/setubal/",
        "aveiro": "https://casasapo.pt/venda-apartamentos/aveiro/",
        "leiria": "https://casasapo.pt/venda-apartamentos/leiria/",
    }
    base_url = REGION_URLS[DEFAULT_REGION]

    def __init__(self, proxy_manager=None, region=None):
        super().__init__(proxy_manager)
        self.region = region or self.DEFAULT_REGION
        self.base_url = self.REGION_URLS.get(self.region, self.REGION_URLS[self.DEFAULT_REGION])
    
    # Multiple selector fallbacks for robustness
    card_selectors = [
        '.property-item',
        '.item',
        '[class*="listing"]',
        '[class*="property"]',
        '[data-testid*="listing"]',
    ]
    
    price_selectors = [
        '.property-price',
        '.price',
        '[class*="price"]',
    ]
    
    title_selectors = [
        '.property-title',
        '.title',
        'h2',
        'h3',
        '[class*="title"]',
    ]
    
    feature_selectors = [
        '.property-features span',
        '.features span',
        'span[class*="feature"]',
    ]
    
    def extract_area_from_text(self, text: str) -> str:
        """Extract area from text using multiple patterns."""
        import re
        if not text:
            return ''
        
        # Try different patterns for area
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*m[²²]',  # 96 m² or 96 m2
            r'(\d+(?:[.,]\d+)?)\s*m2',     # 96 m2
            r'(\d+(?:[.,]\d+)?)\s*sqm',    # 96 sqm
            r'(\d+(?:[.,]\d+)?)\s*m',      # 96 m (context-dependent)
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
            r'T(\d+)',              # T2, T3
            r'(\d+)\s*quartos?',     # 2 quartos
            r'(\d+)\s*bedrooms?',    # 2 bedrooms
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return ''

    async def parse_page(self, page_num: int) -> List[Dict]:
        """Parse listings from current search page with scroll timeout protection."""
        listings = []
        
        # Try each card selector until we find results
        for card_selector in self.card_selectors:
            script = f"""
            (function() {{
                const elements = document.querySelectorAll('{card_selector}');
                const results = [];
                for (let i = 0; i < elements.length; i++) {{
                    const el = elements[i];
                    
                    // Try multiple ways to get link
                    let link = el.querySelector('a');
                    let url = link ? link.href : '';
                    
                    // Try multiple ways to get price
                    let price = el.querySelector('.property-price, .price, [class*="price"], .value');
                    let price_text = price ? price.innerText.trim() : '';
                    if (!price_text) {{
                        // Try to find price in any text containing €
                        const allText = el.innerText || '';
                        const priceMatch = allText.match(/([\\d.]+\\s*€)/);
                        if (priceMatch) price_text = priceMatch[1];
                    }}
                    
                    // Try multiple ways to get title
                    let title = el.querySelector('.property-title, .title, h2, h3, [class*="title"], h4');
                    let title_text = title ? title.innerText.trim() : '';
                    if (!title_text) {{
                        // Try to get title from link text or first heading
                        if (link) title_text = link.innerText.trim();
                        if (!title_text) {{
                            const heading = el.querySelector('h1, h2, h3, h4, h5');
                            if (heading) title_text = heading.innerText.trim();
                        }}
                    }}
                    
                    // Get features
                    const featureSpans = el.querySelectorAll('.property-features span, .features span, span[class*="feature"], .feature');
                    const features = [];
                    for (let j = 0; j < featureSpans.length; j++) {{
                        const text = featureSpans[j].innerText.trim();
                        if (text) features.push(text);
                    }}
                    
                    const descriptionEl = el.querySelector('.description, p, [class*="desc"]');
                    const description = descriptionEl ? descriptionEl.innerText.trim() : '';
                    const fullText = title_text + ' ' + features.join(' ') + ' ' + description;
                    
                    // Get source_id from data attributes
                    let source_id = el.getAttribute('data-id') || el.getAttribute('data-listing-id') || '';
                    
                    results.push({{
                        source_id: source_id,
                        url: url,
                        title: title_text,
                        price_text: price_text,
                        features: features,
                        description: description,
                        full_text: fullText
                    }});
                }}
                return results;
            }})()
            """
            results = await self.safe_evaluate(script, timeout=15.0)
            
            if results and len(results) > 0:
                logger.info(f"[{self.name}] Found {len(results)} listings using selector: {card_selector}")
                
                for data in results:
                    features = data.get('features', [])
                    full_text = data.get('full_text', '')
                    
                    # Try multiple methods to extract area
                    area = next((f for f in features if 'm²' in f or 'm2' in f.lower()), '')
                    if not area:
                        area = self.extract_area_from_text(full_text)
                    
                    # Try multiple methods to extract rooms
                    rooms = next((f for f in features if 'T' in f or 'quarto' in f.lower()), '')
                    if not rooms:
                        rooms = self.extract_rooms_from_text(full_text)
                    
                    # Only add if we have at least some data
                    if data.get('title') or data.get('price_text'):
                        listings.append(self.to_raw_listing({
                            "source_id": data.get("source_id", ""),
                            "url": data.get("url", ""),
                            "title": data.get("title", ""),
                            "price_text": data.get("price_text", ""),
                            "area_text": area,
                            "rooms_text": rooms,
                            "portal": self.name
                        }))
                break
            else:
                logger.debug(f"[{self.name}] No results with selector: {card_selector}")
        
        if not listings:
            logger.warning(f"[{self.name}] No listings found with any selector")
            await self.take_debug_snapshot()
        
        logger.info(f"[{self.name}] Parsed {len(listings)} listings on page {page_num}")
        return listings

    async def get_next_page(self) -> bool:
        """Navigate to next page using URL increment."""
        url = await self.tab.evaluate("window.location.href")
        if '/?p=' in url:
            import re
            new_url = re.sub(r'\?p=\d+', lambda m: f"?p={int(m.group().split('=')[1])+1}", url)
            await self.tab.get(new_url)
        else:
            await self.tab.get(url + "?p=2")
        return True
    
    async def close_browser(self):
        """Close the browser."""
        if self.browser:
            try:
                self.browser.stop()
                logger.info(f"[{self.name}] Browser closed")
            except Exception as e:
                logger.warning(f"[{self.name}] Error closing browser: {e}")
