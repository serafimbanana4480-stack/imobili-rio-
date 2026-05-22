"""Test ValuationEngine with sample data."""
import sys
sys.path.insert(0, '.')

from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.database.repository import DatabaseRepository

def main():
    print("Testing ValuationEngine...")
    
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
        engine = ValuationEngine(repo)
        result = engine.valuate(sample)
        print(f"Sample valuation result: {result}")
        return
    
    print(f"Found {len(listings)} clean listings")
    
    # Test valuation engine
    engine = ValuationEngine(repo)
    
    # Test with first listing
    listing = listings[0]
    sample_data = {
        "preco_pedido": listing.preco_pedido,
        "area_util_m2": listing.area_util_m2,
        "quartos": listing.quartos,
        "casas_banho": listing.casas_banho,
        "concelho": listing.concelho,
        "freguesia": listing.freguesia,
        "distrito": listing.distrito,
        "lat": listing.lat,
        "lon": listing.lon,
    }
    
    print(f"\nTesting with listing: {listing.source_id}")
    print(f"Price: {listing.preco_pedido}, Area: {listing.area_util_m2}, Rooms: {listing.quartos}")
    
    result = engine.valuate(sample_data)
    print(f"Valuation result: {result}")

if __name__ == "__main__":
    main()
