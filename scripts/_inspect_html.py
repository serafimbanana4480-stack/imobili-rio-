"""Inspect live HTML from era/remax/casa_sapo to design real selectors.

For each portal: fetches the listing page, dumps:
  - HTTP status + size
  - all JSON-LD script blocks (trimmed)
  - Next.js __NEXT_DATA__ presence
  - first 3 anchors matching common listing-url patterns
  - snippet of surrounding HTML for the first matched anchor
"""
from __future__ import annotations
import asyncio, re, sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

TARGETS = {
    "era":        "https://www.era.pt/comprar/apartamentos/porto",
    "remax":      "https://www.remax.pt/comprar/apartamento/porto",
    "casa_sapo":  "https://casa.sapo.pt/comprar/apartamentos/porto/",
    "casa_sapo2": "https://casasapo.pt/venda-apartamentos/porto/",
}
URL_PATTERNS = {
    "era":        re.compile(r'href="([^"]*?/imovel/[^"]*?)"'),
    "remax":      re.compile(r'href="([^"]*?/imovel/[^"]*?)"'),
    "casa_sapo":  re.compile(r'href="([^"]*?/(?:detalhes|ver)/[^"]*?\d[^"]*?)"'),
    "casa_sapo2": re.compile(r'href="([^"]*?-\d{5,}\.html[^"]*?)"'),
}

async def inspect(name: str, url: str) -> None:
    pat = URL_PATTERNS.get(name) or re.compile(r'href="([^"]{20,})"')
    async with httpx.AsyncClient(headers=default_headers(), timeout=20.0, follow_redirects=True) as c:
        try:
            r = await c.get(url)
        except Exception as e:
            print(f"\n### {name}: FETCH FAIL {e.__class__.__name__}: {e}")
            return
    body = r.text
    print(f"\n### {name} — {url}")
    print(f"HTTP {r.status_code}, {len(body)} bytes")
    print(f"next_data_present: {'__NEXT_DATA__' in body}")

    # JSON-LD
    jsonld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', body, flags=re.S|re.I)
    print(f"json_ld_scripts: {len(jsonld)}")
    for i, block in enumerate(jsonld[:3]):
        try:
            data = json.loads(block.strip())
        except Exception:
            print(f"  [{i}] invalid JSON ({len(block)} chars)")
            continue
        if isinstance(data, dict):
            keys = list(data.keys())[:8]
        else:
            keys = f"<{type(data).__name__} len={len(data) if hasattr(data,'__len__') else '?'}>"
        print(f"  [{i}] top-keys={keys}")

    # URL anchors
    matches = pat.findall(body)
    unique = list(dict.fromkeys(matches))
    print(f"anchors_matched: {len(matches)} total, {len(unique)} unique (pattern={pat.pattern[:60]})")
    for u in unique[:5]:
        print(f"  → {u[:140]}")

    # Snippet around first anchor
    if unique:
        first = unique[0]
        idx = body.find(first)
        if idx >= 0:
            lo = max(0, idx-400); hi = min(len(body), idx+800)
            snippet = body[lo:hi]
            snippet = re.sub(r"\s+", " ", snippet).strip()
            print(f"\n--- context around first anchor ---")
            print(snippet[:900])
            print(f"--- end context ---")

    # Quick € presence check
    euro_contexts = re.findall(r".{0,60}€.{0,30}", body)
    print(f"\ntotal_€_mentions: {len(euro_contexts)}")
    for e in euro_contexts[:5]:
        print(f"  € | {re.sub(chr(10),' ', e)[:120]}")

async def main():
    for name, url in TARGETS.items():
        await inspect(name, url)

if __name__ == "__main__":
    asyncio.run(main())
