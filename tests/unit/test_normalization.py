"""Test normalization of raw listings."""
from realestate_engine.etl.normalizer import Normalizer
from realestate_engine.database.repository import DatabaseRepository

repo = DatabaseRepository()
raw = repo.get_raw_listings(limit=5)

print('Testing normalization:')
for r in raw:
    print(f'\n{r.source_portal}-{r.source_id}:')
    print(f'  Raw data keys: {list(r.raw_data.keys())}')
    print(f'  price_text: {r.raw_data.get("price_text", "?")}')
    print(f'  area_text: {r.raw_data.get("area_text", "?")}')
    print(f'  rooms_text: {r.raw_data.get("rooms_text", "?")}')
    
    normalized = Normalizer.normalize(r.raw_data, r.source_portal)
    print(f'  Normalized price: {normalized.get("preco_pedido")}')
    print(f'  Normalized area: {normalized.get("area_util_m2")}')
    print(f'  Normalized rooms: {normalized.get("quartos")}')
