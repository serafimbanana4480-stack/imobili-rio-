"""Test ScoringEngine with sample data."""
import sys
sys.path.insert(0, '.')

from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.repository import DatabaseRepository

def main():
    print("Testing ScoringEngine...")
    
    # Get some real listings from database
    repo = DatabaseRepository()
    listings = repo.get_clean_listings(limit=10)
    
    if not listings:
        print("No clean listings found in database. Creating sample data...")
        # Create sample listing for testing
        sample = {
            "preco_pedido": 250000,
            "area_util_m2": 80,
            "quartos": 2,
            "casas_banho": 1,
            "concelho": "Porto",
            "freguesia": "Bonfim",
            "distrito": "Porto",
            "lat": 41.15,
            "lon": -8.61,
            "ano_construcao": 2000,
        }
        engine = ScoringEngine(repo)
        result = engine.score(sample)
        print(f"Sample scoring result: {result}")
        return
    
    print(f"Found {len(listings)} clean listings")
    
    # Test scoring engine
    engine = ScoringEngine(repo)
    
    # Test with first listing
    listing = listings[0]
    print(f"\nTesting with listing: {listing.source_id}")
    print(f"Price: {listing.preco_pedido}, Area: {listing.area_util_m2}, Rooms: {listing.quartos}")
    
    result = engine.score(listing)
    print(f"Scoring result: {result}")

if __name__ == "__main__":
    main()
