
import sys
import os
import asyncio
from sqlalchemy import text
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, RawListing

async def cleanup_database():
    repo = DatabaseRepository()
    session = repo.Session()
    
    print("Starting database cleanup...")
    
    # 1. Identify listings with empty source_id in clean_listings
    empty_clean = session.query(CleanListing).filter(CleanListing.source_id == '').all()
    print(f"Found {len(empty_clean)} clean listings with empty source_id")
    
    # 2. Try to recover source_id from raw_listings if possible
    # This is hard because they don't have a direct foreign key that is stable if ID was lost
    # But maybe we can match by URL?
    recovered = 0
    for clean in empty_clean:
        if clean.source_url:
            raw = session.query(RawListing).filter(RawListing.source_url == clean.source_url).first()
            if raw and raw.source_id:
                clean.source_id = raw.source_id
                recovered += 1
    
    print(f"Recovered {recovered} source_ids from raw listings")
    session.commit()
    
    # 3. Remove actual duplicates (same portal + same source_id)
    # Keep the one with most recent updated_at
    dupes = session.execute(text("""
        SELECT source_portal, source_id, count(*) 
        FROM clean_listings 
        WHERE source_id != ''
        GROUP BY source_portal, source_id 
        HAVING count(*) > 1
    """)).all()
    
    print(f"Found {len(dupes)} duplicate ID sets in clean_listings")
    
    removed_dupes = 0
    for portal, sid, count in dupes:
        # Get all records for this dupe
        records = session.query(CleanListing).filter(
            CleanListing.source_portal == portal,
            CleanListing.source_id == sid
        ).order_by(CleanListing.updated_at.desc()).all()
        
        # Keep the first one, delete the rest
        to_delete = records[1:]
        for r in to_delete:
            session.delete(r)
            removed_dupes += 1
            
    print(f"Removed {removed_dupes} duplicate listings")
    session.commit()
    
    # 4. Remove listings that still have empty source_id (they are unusable)
    remaining_empty = session.query(CleanListing).filter(CleanListing.source_id == '').count()
    if remaining_empty > 0:
        session.execute(text("DELETE FROM clean_listings WHERE source_id = ''"))
        print(f"Deleted {remaining_empty} remaining listings with empty source_id")
        session.commit()

    session.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(cleanup_database())
