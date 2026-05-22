"""Test geocoding with new settings (30s timeout, 15-fail threshold, rate limiting)."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.etl.geocoder import Geocoder


def main() -> int:
    print("Testing geocoding with new settings...")
    print("  - Timeout: 30s (was 10s)")
    print("  - Circuit breaker: 15 failures (was 5)")
    print("  - Rate limiting: 1 request/second")
    print()
    
    geocoder = Geocoder()
    
    # Test addresses (Portuguese cities)
    test_addresses = [
        "Lisboa, Lisboa",
        "Porto, Porto",
        "Braga, Braga",
        "Faro, Faro",
        "Coimbra, Coimbra",
    ]
    
    print(f"Testing {len(test_addresses)} addresses...")
    print()
    
    success_count = 0
    for i, address in enumerate(test_addresses, 1):
        print(f"[{i}/{len(test_addresses)}] Geocoding: {address}")
        coords = geocoder.geocode(address)
        if coords:
            print(f"  ✅ SUCCESS: {coords}")
            success_count += 1
        else:
            print(f"  ❌ FAILED")
        print()
    
    print(f"=== Results ===")
    print(f"Success: {success_count}/{len(test_addresses)}")
    print(f"Failure: {len(test_addresses) - success_count}/{len(test_addresses)}")
    
    return 0 if success_count >= len(test_addresses) * 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
