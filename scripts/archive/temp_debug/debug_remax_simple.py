"""Simple debug for REMAX page."""
import asyncio
import sys
sys.path.insert(0, '.')

import httpx
from realestate_engine.scraping.http_client import default_headers, pick_user_agent

async def main():
    url = "https://remax.pt/pt/imoveis/venda-apartamento-t4-lisboa-campolide/120261243-157"
    
    headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
    timeout = httpx.Timeout(45.0, connect=15.0)
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True, http2=False) as client:
        resp = await client.get(url, headers={"User-Agent": pick_user_agent()})
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Check for patterns
        print(f"Has __NEXT_DATA__: {'__NEXT_DATA__' in resp.text}")
        print(f"Has ld+json: {'application/ld+json' in resp.text}")
        print(f"Has price: {'price' in resp.text.lower()}")
        print(f"Has euro: {'€' in resp.text}")
        
        # Look for any JSON in script tags
        import re
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        print(f"\nFound {len(script_matches)} script tags")
        
        for i, script in enumerate(script_matches):
            if 'application/json' in script or 'application/ld' in script or '__NEXT_DATA__' in script:
                print(f"\n--- Script {i} (potential JSON) ---")
                print(f"Length: {len(script)}")
                print(f"Preview: {script[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
