"""Debug REMAX HTML structure."""
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
        
        # Save HTML for inspection
        with open("remax_debug.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        
        # Check for common patterns
        if "__NEXT_DATA__" in resp.text:
            print("✓ Found __NEXT_DATA__")
        if "application/ld+json" in resp.text:
            print("✓ Found application/ld+json")
        if '"price"' in resp.text.lower():
            print("✓ Found price in HTML")
        if '"area"' in resp.text.lower() or '"m²"' in resp.text:
            print("✓ Found area in HTML")
        
        # Look for JSON data
        import re
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if next_data_match:
            print(f"\n__NEXT_DATA__ found, length: {len(next_data_match.group(1))}")
            # Try to parse it
            import json
            try:
                data = json.loads(next_data_match.group(1))
                print(f"Keys: {list(data.keys())}")
                if "props" in data:
                    print(f"props keys: {list(data['props'].keys())}")
            except Exception as e:
                print(f"Error parsing __NEXT_DATA__: {e}")

if __name__ == "__main__":
    asyncio.run(main())
