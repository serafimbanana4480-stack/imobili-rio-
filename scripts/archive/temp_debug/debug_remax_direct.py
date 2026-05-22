"""Debug REMAX Direct spider to see why listings are being skipped."""
import asyncio
import sys
import json
sys.path.insert(0, '.')

from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider
import httpx
from realestate_engine.scraping.http_client import default_headers, pick_user_agent

async def main():
    spider = REMAXDirectSpider()
    
    # Get one candidate URL and debug the parsing
    headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
    timeout = httpx.Timeout(45.0, connect=15.0)
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True, http2=False) as client:
        # Get sitemap
        candidates = await spider._discover_listing_urls(client, 100)
        print(f"Found {len(candidates)} candidate URLs")
        
        if candidates:
            # Test first URL
            test_url = candidates[0]
            print(f"\nTesting URL: {test_url}")
            
            resp = await client.get(test_url, headers={"User-Agent": pick_user_agent()})
            print(f"Status: {resp.status_code}")
            
            # Try to extract JSON-LD
            import re
            LD_JSON_RE = re.compile(
                r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
                re.DOTALL | re.IGNORECASE,
            )
            
            blocks = LD_JSON_RE.findall(resp.text)
            print(f"Found {len(blocks)} JSON-LD blocks")
            
            for i, block in enumerate(blocks[:3]):
                print(f"\n--- Block {i+1} ---")
                try:
                    data = json.loads(block.strip())
                    print(f"Type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:10]}")
                        if "@type" in data:
                            print(f"@type: {data['@type']}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"First item type: {data[0].get('@type', 'unknown')}")
                        print(f"First item keys: {list(data[0].keys())[:10]}")
                except Exception as e:
                    print(f"Error parsing: {e}")

if __name__ == "__main__":
    asyncio.run(main())
