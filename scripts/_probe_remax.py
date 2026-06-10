import re, pathlib, json
t = pathlib.Path("data/cache/html_samples/remax.html").read_text(encoding="utf-8", errors="replace")
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
print("NEXT_DATA found:", bool(m), "len:", len(m.group(1)) if m else 0)
if m:
    d = json.loads(m.group(1))
    print("top keys:", list(d.keys())[:10])
    pp = d.get("props", {}); pg = pp.get("pageProps", {})
    print("pageProps keys:", list(pg.keys())[:30])
    # walk for anything list-like
    def walk(node, path="", depth=0):
        if depth > 6: return
        if isinstance(node, dict):
            for k, v in node.items():
                newp = f"{path}.{k}"
                if isinstance(v, list) and len(v) > 3 and isinstance(v[0], dict):
                    print(f"  LIST at {newp}: {len(v)} items, sample keys: {list(v[0].keys())[:10]}")
                walk(v, newp, depth+1)
        elif isinstance(node, list):
            for i, item in enumerate(node[:2]):
                walk(item, f"{path}[{i}]", depth+1)
    walk(pg, "pageProps")
