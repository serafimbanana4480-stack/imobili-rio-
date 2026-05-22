"""Imovirtual spider using Nodriver."""
from typing import List, Dict
from loguru import logger

from realestate_engine.scraping.spiders.base_spider_nodriver import BaseSpiderNodriver


class ImovirtualSpider(BaseSpiderNodriver):
    """Spider for imovirtual.pt with JSON extraction and DOM fallback."""
    
    name = "imovirtual"
    base_url = "https://www.imovirtual.com/comprar/apartamento/porto/"
    
    # DOM fallback selectors
    card_selectors = [
        '[class*="listing"]',
        '[class*="property"]',
        '.listing-card',
        '[data-testid*="listing"]',
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
    
    async def extract_api_response(self) -> List[Dict]:
        """Extract listings from Imovirtual API if accessible."""
        script = """
        async function fetchAPI() {
            try {
                // This is a placeholder for actual API call
                return null;
            } catch(e) {
                return null;
            }
        }
        return await fetchAPI();
        """
        results = await self.safe_evaluate(script)
        return results or []

    async def parse_page(self, page_num: int) -> List[Dict]:
        """Extract data from JSON, API, or DOM."""
        listings = []
        
        # Try JSON extraction first (Layer 1)
        try:
            script_content = await self.safe_evaluate("document.getElementById('__NEXT_DATA__')?.innerText", timeout=10.0)
            if script_content:
                import json
                data = json.loads(script_content)
                
                # Try multiple possible paths in the JSON
                possible_paths = [
                    lambda d: d['props']['pageProps']['listings']['regular'] + d['props']['pageProps']['listings'].get('promoted', []),
                    lambda d: d.get('props', {}).get('pageProps', {}).get('listings', {}).get('regular', []),
                    lambda d: d.get('props', {}).get('pageProps', {}).get('listings', []),
                ]
                
                for path_func in possible_paths:
                    try:
                        items = path_func(data)
                        if items:
                            logger.info(f"[{self.name}] Found {len(items)} items via JSON extraction")
                            for item in items:
                                title = item.get('title', '')
                                area_text = str(item.get('area', ''))
                                rooms_text = str(item.get('roomsNumber', ''))
                                
                                # Fallback to text extraction if area/rooms missing
                                if not area_text or area_text == 'None' or area_text == '':
                                    area_text = self.extract_area_from_text(title)
                                if not rooms_text or rooms_text == 'None' or rooms_text == '':
                                    rooms_text = self.extract_rooms_from_text(title)
                                
                                listings.append(self.to_raw_listing({
                                    "source_id": str(item.get('id', '')),
                                    "url": item.get('url', ''),
                                    "title": title,
                                    "price_text": str(item.get('price', {}).get('value', '')),
                                    "area_text": area_text,
                                    "rooms_text": rooms_text,
                                    "location": item.get('location', {}).get('address', {}).get('displayString', ''),
                                    "portal": self.name,
                                    "raw_item": item
                                }))
                            break
                    except (KeyError, TypeError):
                        continue
                
                if listings:
                    logger.info(f"[{self.name}] JSON extraction successful: {len(listings)} listings")
                    return listings
        except Exception as e:
            logger.warning(f"[{self.name}] JSON extraction failed: {e}")
            
        # Layer 2: API extraction
        api_results = await self.extract_api_response()
        if api_results:
             logger.info(f"[{self.name}] API extraction successful: {len(api_results)} listings")
             # Process api_results...
             return listings

        # Fallback to DOM parsing (Layer 3)
        
        for card_selector in self.card_selectors:
            script = f"""
            Array.from(document.querySelectorAll('{card_selector}')).map(el => {{
                const link = el.querySelector('a');
                const price = el.querySelector('[class*="price"]');
                const title = el.querySelector('h2, h3, [class*="title"]');
                const description = el.querySelector('.description, p, [class*="desc"]')?.innerText.trim() || '';
                const fullText = (title?.innerText || '') + ' ' + description;
                return {{
                    source_id: el.getAttribute('data-id') || '',
                    url: link ? link.href : '',
                    title: title ? title.innerText.trim() : '',
                    price_text: price ? price.innerText.trim() : '',
                    description: description,
                    full_text: fullText
                }};
            }});
            """
            results = await self.safe_evaluate(script, timeout=15.0)
            
            if results and len(results) > 0:
                logger.info(f"[{self.name}] DOM parsing found {len(results)} listings with selector: {card_selector}")
                for data in results:
                    full_text = data.get('full_text', '')
                    area = self.extract_area_from_text(full_text)
                    rooms = self.extract_rooms_from_text(full_text)
                    
                    listings.append(self.to_raw_listing({
                        **data,
                        "area_text": area,
                        "rooms_text": rooms,
                        "portal": self.name
                    }))
                break
        
        if not listings:
            logger.warning(f"[{self.name}] No listings found with JSON or DOM parsing")
            await self.take_debug_snapshot()
        
        logger.info(f"[{self.name}] Parsed {len(listings)} listings on page {page_num}")
        return listings

    async def get_next_page(self) -> bool:
        """Update URL for next page or click button."""
        try:
            # Imovirtual uses query params or button
            url = await self.tab.evaluate("window.location.href")
            if '?' in url:
                if 'page=' in url:
                    # Increment page
                    import re
                    new_url = re.sub(r'page=\d+', lambda m: f"page={int(m.group().split('=')[1])+1}", url)
                    await self.tab.get(new_url)
                else:
                    await self.tab.get(url + "&page=2")
            else:
                await self.tab.get(url + "?page=2")
            return True
        except:
            return False
    
    async def close_browser(self):
        """Close the browser."""
        if self.browser:
            try:
                self.browser.stop()
                logger.info(f"[{self.name}] Browser closed")
            except Exception as e:
                logger.warning(f"[{self.name}] Error closing browser: {e}")
