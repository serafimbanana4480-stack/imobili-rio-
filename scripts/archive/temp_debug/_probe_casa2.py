import pathlib, re, json, collections
t = pathlib.Path("data/cache/html_samples/casa_sapo.html").read_text(encoding="utf-8", errors="replace")
# casa.sapo.pt encodes the "+" as &#x2B; — match both raw and entity-encoded.
blocks = re.findall(
    r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
    t, re.S | re.I,
)
print("ld+json blocks:", len(blocks))
types = collections.Counter()
offers = []
for b in blocks:
    try:
        d = json.loads(b.strip())
    except Exception:
        continue
    if isinstance(d, dict):
        types[d.get("@type", "?")] += 1
        if d.get("@type") == "Offer":
            offers.append(d)
    elif isinstance(d, list):
        for x in d:
            if isinstance(x, dict):
                types[x.get("@type", "?")] += 1
                if x.get("@type") == "Offer":
                    offers.append(x)
print("types:", dict(types))
print("offers:", len(offers))
if offers:
    o = offers[0]
    print("sample offer keys:", list(o.keys()))
    print("sample name:", o.get("name"))
    print("sample price:", o.get("price"))
    print("sample loc:", (o.get("availableAtOrFrom") or {}).get("address"))
    print("sample geo:", (o.get("availableAtOrFrom") or {}).get("geo"))
    print("sample desc:", (o.get("description") or "")[:200])
