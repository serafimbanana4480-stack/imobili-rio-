"""Test multi-provider geocoding."""
import sys
sys.path.insert(0, '.')

from realestate_engine.etl.geocoder import Geocoder

def main():
    geocoder = Geocoder()
    
    # Test with real Portuguese addresses
    test_addresses = [
        "Porto, Portugal",
        "Lisboa, Portugal",
        "Rua do Almada, Porto",
        "Avenida da Liberdade, Lisboa",
    ]
    
    print("Testing multi-provider geocoding...")
    for addr in test_addresses:
        coords = geocoder.geocode(addr)
        print(f"{addr}: {coords}")
    
    print("\nGeocoding test complete")

if __name__ == "__main__":
    main()
