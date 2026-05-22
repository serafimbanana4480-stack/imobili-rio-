"""Try alternative REMAX endpoints that might return listings directly."""
import asyncio, sys, pathlib, re, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

CANDIDATES = [
    # Standard search
    "https://www.remax.pt/comprar/apartamento/porto",
    # Sitemap (often public)
    "https://www.remax.pt/sitemap.xml",
    "https://www.remax.pt/sitemaps/listings.xml",
    "https://www.remax.pt/sitemap-listings.xml",
    # Known public REMAX APIs (from community reports)
    "https://www.remax.pt/api/search?listingClass=1&businessType=1&regionId1=0",
    "https://backend.remax.pt/listings/search?page=1&pageSize=20&businessTypeID=1",
    "https://searchapi.remax.pt/api/Listings?businessTypeID=1",
]

async def main():
    async with httpx.AsyncClient(headers=default_headers(), timeout=15.0, follow_redirects=True) as c:
        for url in CANDIDATES:
            try:
                r = await c.get(url)
                size = len(r.content)
                ct = r.headers.get("content-type", "")
                is_json = "json" in ct.lower()
                sample = r.text[:200].replace("\n", " ")
                print(f"{r.status_code} | {size:7d}B | {ct[:30]:30s} | {url}")
                if is_json and r.status_code == 200:
                    try:
                        j = r.json()
                        print(f"     JSON keys: {list(j.keys())[:8] if isinstance(j, dict) else f'list len={len(j)}'}")
                    except Exception:
                        pass
                elif "<loc>" in r.text:
                    locs = re.findall(r"<loc>([^<]+)</loc>", r.text)[:5]
                    for l in locs: print(f"     sitemap loc: {l}")
            except Exception as e:
                print(f"ERR | {url} → {e.__class__.__name__}: {e}")

asyncio.run(main())
