"""Clean up clean listings with empty source_id."""
from realestate_engine.database.repository import DatabaseRepository

repo = DatabaseRepository()
clean = repo.get_clean_listings(limit=1000)
empty_source_ids = [c for c in clean if not c.source_id or c.source_id.strip() == ""]

print(f'Total clean listings: {len(clean)}')
print(f'Clean listings with empty source_id: {len(empty_source_ids)}')

if empty_source_ids:
    # Delete them
    with repo.Session() as session:
        for listing in empty_source_ids:
            session.delete(listing)
        session.commit()
    print(f'Deleted {len(empty_source_ids)} clean listings with empty source_id')
else:
    print('No clean listings with empty source_id found')
