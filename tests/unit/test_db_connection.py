"""Test database connection from API perspective."""
import sys
sys.path.insert(0, '.')

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.utils.config import config

print(f"Database URL: {config.database_url}")

repo = DatabaseRepository()
print(f"Repository engine: {repo.engine}")

# Try to query clean_listings
try:
    listings = repo.get_clean_listings(limit=1)
    print(f"Success! Found {len(listings)} listings")
except Exception as e:
    print(f"Error: {e}")
