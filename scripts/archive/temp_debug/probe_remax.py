
import httpx
import re
import asyncio

async def probe_remax():
    url = "https://www.remax.pt/imoveis/venda-apartamento-t2-porto-cedofeita/120141071-449"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        
        with open("remax_detail.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
            
        # Look for script tags
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        print(f"Found {len(scripts)} script tags")
        
        for i, s in enumerate(scripts):
            if "application/ld+json" in resp.text: # check outer
                pass
            if "@type" in s:
                print(f"Script {i} contains @type: {s[:100]}...")
            if "__NEXT_DATA__" in s:
                print(f"Script {i} contains __NEXT_DATA__")

if __name__ == "__main__":
    asyncio.run(probe_remax())
