
import sys
import os
import asyncio
from sqlalchemy import func
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing

async def find_duplicates():
    repo = DatabaseRepository()
    session = repo.Session()
    
    dupes = session.query(
        CleanListing.source_portal, CleanListing.source_id, func.count('*').label('cnt')
    ).group_by(
        CleanListing.source_portal, CleanListing.source_id
    ).having(func.count('*') > 1).all()
    
    print(f"Found {len(dupes)} sets of duplicates in clean_listings")
    if dupes:
        print("Sample duplicates (Portal, ID, Count):")
        for d in dupes[:5]:
            print(f"- {d[0]}, {d[1]}, {d[2]}")
            
    session.close()

if __name__ == "__main__":
    asyncio.run(find_duplicates())
