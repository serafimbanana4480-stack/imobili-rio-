import re, pathlib, json
t = pathlib.Path("data/cache/html_samples/remax.html").read_text(encoding="utf-8", errors="replace")
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
d = json.loads(m.group(1))
pg = d["props"]["pageProps"]
for k in ("initialSearchResultsInfo", "initialSearchResultsInfoSimilarEntities"):
    v = pg.get(k)
    print(f"{k}: type={type(v).__name__}, ", end="")
    if isinstance(v, dict):
        print(f"keys={list(v.keys())[:20]}")
    elif isinstance(v, list):
        print(f"len={len(v)}")
    else:
        print(repr(v)[:200])

# Also search for API endpoints in the raw HTML
apis = set(re.findall(r'https?://[a-z0-9.-]*remax[a-z0-9.-]*/[^\s"\'<>]{5,120}', t))
print("\nAPI-ish URLs found (remax domain):")
for a in sorted(apis)[:30]:
    print(" ", a)

# Look for any large list in the JSON
def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        if node and isinstance(node[0], dict) and len(node) >= 3:
            keys = set()
            for item in node[:3]:
                if isinstance(item, dict): keys |= set(item.keys())
            if any(k.lower() in ("id","price","listingid","listingprice","listingnumber","listingtitle") for k in keys):
                print(f"\nCANDIDATE LIST at {path}: len={len(node)}")
                print(f"  sample[0] keys: {list(node[0].keys())[:20]}")
                print(f"  sample[0]: {json.dumps(node[0])[:500]}")
        for i, item in enumerate(node[:2]):
            walk(item, f"{path}[{i}]")

walk(d, "")
