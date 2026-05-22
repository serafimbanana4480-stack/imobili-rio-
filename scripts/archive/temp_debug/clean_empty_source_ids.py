"""Clean up raw listings with empty source_id."""
from realestate_engine.database.repository import DatabaseRepository

repo = DatabaseRepository()

# Get all raw listings with empty source_id
raw = repo.get_raw_listings(limit=1000)
empty_source_ids = [r for r in raw if not r.source_id or r.source_id.strip() == ""]

print(f'Total raw listings: {len(raw)}')
print(f'Listings with empty source_id: {len(empty_source_ids)}')

if empty_source_ids:
    # Delete them
    with repo.Session() as session:
        for listing in empty_source_ids:
            session.delete(listing)
        session.commit()
    print(f'Deleted {len(empty_source_ids)} raw listings with empty source_id')
else:
    print('No listings with empty source_id found')
