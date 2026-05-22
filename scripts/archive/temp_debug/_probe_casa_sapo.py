"""Deep-inspect casa.sapo.pt HTML to find the real listing container/fields."""
import pathlib, re

t = pathlib.Path("data/cache/html_samples/casa_sapo.html").read_text(encoding="utf-8", errors="replace")
print("size:", len(t))
print("itemscope count:", t.count("itemscope"))
print("itemtype mentions:", len(re.findall(r'itemtype="[^"]+"', t)))
# Show distinct itemtype values
for v in sorted(set(re.findall(r'itemtype="([^"]+)"', t))):
    print(" itemtype:", v)

# Find data-* attributes on cards
for attr in ("data-id", "data-listing-id", "data-property-id", "data-ad-id", "data-testid"):
    matches = re.findall(rf'{attr}="([^"]+)"', t)
    if matches:
        print(f"{attr}: {len(matches)} (sample {matches[:5]})")

# Look for a price-containing element + enclosing structure
first_price = re.search(r'"price":\["([\d. ]+€)"\]', t)
if first_price:
    i = first_price.start()
    print(f"\nFirst embedded price at index {i}: {first_price.group(1)}")
    print("---context ±600---")
    ctx = t[max(0, i-600):i+600]
    ctx = re.sub(r"\s+", " ", ctx)
    print(ctx)

# Find a typical listing card: repeated pattern. Try itemprop="url" anchors
url_items = re.findall(r'<a[^>]*itemprop="url"[^>]*href="([^"]+)"', t)
print(f"\nitemprop=url anchors: {len(url_items)}")
for u in url_items[:5]: print(" ", u)

# Try another common pattern on casa.sapo.pt: anchors to /detalhes/
det = re.findall(r'href="(https?://[^"]*?/(?:detalhes|venda|casas?/comprar|imovel)[^"]*?)"', t)
print(f"/detalhes/ anchors: {len(set(det))}")
for u in sorted(set(det))[:5]: print(" ", u)

# Numeric IDs
ids = re.findall(r'\b([A-Z]{2,4}[- ]?\d{6,}|\d{7,})\b', t)
print(f"possible IDs: {len(set(ids))} unique, samples: {list(set(ids))[:10]}")
