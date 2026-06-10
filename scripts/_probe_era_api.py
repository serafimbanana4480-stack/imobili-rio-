"""Brute-probe common DNN (DotNetNuke) SearchList API endpoints on era.pt."""
import asyncio, sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

CANDIDATES = [
    "https://www.era.pt/API/SearchList/Search/List",
    "https://www.era.pt/API/SearchList/Search/Query",
    "https://www.era.pt/API/SearchList/Search/Results",
    "https://www.era.pt/API/SearchList/Listings/Search",
    "https://www.era.pt/API/SearchList/Listings/Query",
    "https://www.era.pt/API/Search/List",
    "https://www.era.pt/API/ServicesModule/SearchList/Search",
    "https://www.era.pt/API/ServicesModule/SearchList/Listings",
    "https://www.era.pt/DesktopModules/SearchList/API/Search/Query",
    "https://www.era.pt/DesktopModules/SearchList/API/Listings/List",
    # params-first variants
    "https://www.era.pt/API/SearchList/Search?type=apartamento&region=porto",
    "https://www.era.pt/API/ServicesModule/Search/List?component=SearchList",
]

async def main():
    headers = default_headers()
    headers["Accept"] = "application/json, text/plain, */*"
    async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as c:
        for url in CANDIDATES:
            try:
                r = await c.get(url)
            except Exception as e:
                print(f"ERR | {url} → {e.__class__.__name__}")
                continue
            ct = r.headers.get("content-type", "")
            print(f"{r.status_code} | {len(r.content):7d}B | {ct[:30]:30s} | {url}")
            if r.status_code == 200 and "json" in ct.lower():
                try:
                    j = r.json()
                    print("    → keys:", list(j.keys())[:10] if isinstance(j, dict) else f"list len={len(j)}")
                except Exception:
                    pass

asyncio.run(main())
