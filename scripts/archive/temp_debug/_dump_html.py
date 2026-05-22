"""Dump raw HTML pages to data/cache/ for offline inspection."""
import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

OUT = pathlib.Path("data/cache/html_samples")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = {
    "era":       "https://www.era.pt/comprar/apartamentos/porto",
    "remax":     "https://www.remax.pt/comprar/apartamento/porto",
    "casa_sapo": "https://casa.sapo.pt/comprar/apartamentos/porto/",
}

async def main():
    for name, url in TARGETS.items():
        async with httpx.AsyncClient(headers=default_headers(), timeout=20.0, follow_redirects=True) as c:
            r = await c.get(url)
        path = OUT / f"{name}.html"
        path.write_bytes(r.content)
        print(f"{name}: HTTP {r.status_code} → {path} ({len(r.content)} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
