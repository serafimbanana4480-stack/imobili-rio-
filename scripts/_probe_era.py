"""Look for ERA AJAX endpoints hidden in the search page JS."""
import asyncio, sys, pathlib, re, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx
from realestate_engine.scraping.http_client import default_headers

async def main():
    async with httpx.AsyncClient(headers=default_headers(), timeout=25.0, follow_redirects=True) as c:
        r = await c.get("https://www.era.pt/comprar/apartamentos/porto")
        body = r.text
        # Search for AJAX endpoints / API patterns
        patterns = [
            (r'["\'](/api/[^"\']+)["\']',      "/api/"),
            (r'["\'](/_api/[^"\']+)["\']',     "/_api/"),
            (r'["\'](/services/[^"\']+)["\']', "/services/"),
            (r'["\'](/desktopmodules/[^"\']+)["\']', "/desktopmodules/"),
            (r'renderSearchList\(["\']([^"\']+)["\']', "renderSearchList("),
            (r'dataSource\s*[=:]\s*["\']([^"\']+)["\']', "dataSource"),
            (r'ajax\w*\s*:\s*["\']([^"\']+)["\']', "ajax:"),
            (r'SearchList\s*[:=]\s*["\']([^"\']+)["\']', "SearchList"),
            (r'url\s*[:=]\s*["\']([^"\']+\.asmx[^"\']*)["\']', ".asmx"),
            (r'url\s*[:=]\s*["\']([^"\']+\.ashx[^"\']*)["\']', ".ashx"),
        ]
        for pat, label in patterns:
            matches = re.findall(pat, body, re.I)
            if matches:
                print(f"\n{label}: {len(matches)}")
                for m in matches[:8]: print("  ", m[:180])
        # Search for listing endpoints explicitly
        for term in ("listing", "imovel", "property", "search"):
            for m in re.findall(rf'["\']([^"\']*{term}[^"\']*\.(?:aspx|asmx|ashx|json)[^"\']*)["\']', body, re.I)[:6]:
                print(f"  {term}→{m[:180]}")

asyncio.run(main())
