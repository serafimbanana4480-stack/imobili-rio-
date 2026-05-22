"""Fetch REMAX sitemap + sample 1 listing detail page, inspect for JSON-LD / NEXT_DATA."""
import asyncio, sys, pathlib, gzip, re, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

async def main():
    async with httpx.AsyncClient(headers=default_headers(), timeout=30.0, follow_redirects=True) as c:
        r = await c.get("https://remax.pt/sitemap/listings_details_pt_1.xml.gz")
        print("sitemap status:", r.status_code, "size:", len(r.content))
        try:
            xml = gzip.decompress(r.content).decode("utf-8", errors="replace")
        except Exception:
            xml = r.text
        urls = re.findall(r"<loc>([^<]+)</loc>", xml)
        print(f"sitemap urls: {len(urls)}; first 3:")
        for u in urls[:3]: print(" ", u)
        # Sample one detail page
        detail_url = urls[0]
        r2 = await c.get(detail_url)
        print(f"\ndetail status: {r2.status_code}, size: {len(r2.content)}")
        has_nd = "__NEXT_DATA__" in r2.text
        print("has __NEXT_DATA__:", has_nd)
        if has_nd:
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r2.text, re.S)
            nd = json.loads(m.group(1))
            pg = nd.get("props", {}).get("pageProps", {})
            print("pageProps keys:", list(pg.keys())[:30])
            # find listing-ish nested object
            def walk(node, path="", depth=0):
                if depth > 5: return
                if isinstance(node, dict):
                    if "listingPrice" in node or ("listingID" in node and "title" in node) or "listingTitle" in node:
                        print(f"\nCANDIDATE at {path}: keys={list(node.keys())[:25]}")
                        print(json.dumps(node, ensure_ascii=False)[:1500])
                        return
                    for k, v in node.items():
                        walk(v, f"{path}.{k}", depth+1)
                elif isinstance(node, list):
                    for i, x in enumerate(node[:2]):
                        walk(x, f"{path}[{i}]", depth+1)
            walk(pg, "pageProps")
        # JSON-LD on detail
        blocks = re.findall(r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>', r2.text, re.S | re.I)
        print(f"\nld+json blocks on detail: {len(blocks)}")
        for b in blocks[:2]:
            try:
                d = json.loads(b.strip())
                print(" @type:", d.get("@type"), "keys:", list(d.keys())[:15] if isinstance(d, dict) else "list")
                print(" ", json.dumps(d, ensure_ascii=False)[:800])
            except Exception:
                pass

asyncio.run(main())
