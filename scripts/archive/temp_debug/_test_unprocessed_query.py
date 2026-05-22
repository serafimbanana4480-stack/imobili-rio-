"""Test the get_unprocessed_raw_listings query."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.database.repository import DatabaseRepository


def main() -> int:
    print("Testing get_unprocessed_raw_listings query...")
    
    repo = DatabaseRepository()
    
    # Test with small limit
    print("Fetching 10 unprocessed raw_listings...")
    unprocessed = repo.get_unprocessed_raw_listings(limit=10)
    
    print(f"Found {len(unprocessed)} unprocessed raw_listings")
    
    for i, raw in enumerate(unprocessed[:5], 1):
        print(f"  {i}. {raw.source_portal} / {raw.source_id} - {raw.created_at}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
