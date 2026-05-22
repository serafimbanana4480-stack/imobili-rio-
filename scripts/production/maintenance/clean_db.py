"""Unified database cleaning script with multiple modes.

This script consolidates the functionality of:
- clean_db.py: Clean raw listings with empty area_text
- clean_clean_source_ids.py: Clean listings with empty source_id
- clean_empty_source_ids.py: Clean raw listings with empty source_id
- cleanup_db.py: Comprehensive cleanup with recovery and deduplication

Usage:
    python clean_db.py raw-empty-area
    python clean_db.py clean-empty-source
    python clean_db.py raw-empty-source
    python clean_db.py full
"""
import sys
import os
import asyncio
from sqlalchemy import text

sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))).replace('\\production\\maintenance', ''))

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, RawListing


async def mode_raw_empty_area():
    """Remove raw listings with empty area_text."""
    import sqlite3
    import json
    
    print("Cleaning raw listings with empty area_text...")
    
    conn = sqlite3.connect('data/db/realestate.db')
    cursor = conn.cursor()
    
    # Check current state
    cursor.execute('SELECT COUNT(*) FROM raw_listings')
    total_raw = cursor.fetchone()[0]
    print(f"Total raw listings before cleanup: {total_raw}")
    
    # Delete raw listings with empty area_text
    cursor.execute('''
        DELETE FROM raw_listings
        WHERE json_extract(raw_data, '$.area_text') IS NULL
        OR json_extract(raw_data, '$.area_text') = ''
        OR json_extract(raw_data, '$.area_text') = ' '
    ''')
    deleted_raw = cursor.rowcount
    print(f"Deleted {deleted_raw} raw listings with empty areas")
    
    # Also delete from clean_listings to start fresh
    cursor.execute('DELETE FROM clean_listings')
    deleted_clean = cursor.rowcount
    print(f"Deleted {deleted_clean} clean listings")
    
    conn.commit()
    
    # Check final state
    cursor.execute('SELECT COUNT(*) FROM raw_listings')
    total_raw_after = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM clean_listings')
    total_clean_after = cursor.fetchone()[0]
    
    print(f"\nTotal raw listings after cleanup: {total_raw_after}")
    print(f"Total clean listings after cleanup: {total_clean_after}")
    
    conn.close()
    print("\nDatabase cleanup completed!")


async def mode_clean_empty_source():
    """Remove clean listings with empty source_id."""
    print("Cleaning clean listings with empty source_id...")
    
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


async def mode_raw_empty_source():
    """Remove raw listings with empty source_id."""
    print("Cleaning raw listings with empty source_id...")
    
    repo = DatabaseRepository()
    raw = repo.get_raw_listings(limit=1000)
    empty_source_ids = [r for r in raw if not r.source_id or r.source_id.strip() == ""]
    
    print(f'Total raw listings: {len(raw)}')
    print(f'Raw listings with empty source_id: {len(empty_source_ids)}')
    
    if empty_source_ids:
        # Delete them
        with repo.Session() as session:
            for listing in empty_source_ids:
                session.delete(listing)
            session.commit()
        print(f'Deleted {len(empty_source_ids)} raw listings with empty source_id')
    else:
        print('No raw listings with empty source_id found')


async def mode_full():
    """Comprehensive cleanup with recovery and deduplication."""
    print("Starting comprehensive database cleanup...")
    
    repo = DatabaseRepository()
    session = repo.Session()
    
    # 1. Identify listings with empty source_id in clean_listings
    empty_clean = session.query(CleanListing).filter(CleanListing.source_id == '').all()
    print(f"Found {len(empty_clean)} clean listings with empty source_id")
    
    # 2. Try to recover source_id from raw_listings if possible
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
    print("Comprehensive cleanup complete.")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python clean_db.py <mode>")
        print("\nModes:")
        print("  raw-empty-area      - Clean raw listings with empty area_text")
        print("  clean-empty-source  - Clean listings with empty source_id")
        print("  raw-empty-source   - Clean raw listings with empty source_id")
        print("  full                - Comprehensive cleanup with recovery and deduplication")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "raw-empty-area":
        await mode_raw_empty_area()
    elif mode == "clean-empty-source":
        await mode_clean_empty_source()
    elif mode == "raw-empty-source":
        await mode_raw_empty_source()
    elif mode == "full":
        await mode_full()
    else:
        print(f"Error: Unknown mode '{mode}'")
        print("Available modes: raw-empty-area, clean-empty-source, raw-empty-source, full")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
