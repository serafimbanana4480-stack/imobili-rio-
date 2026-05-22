"""Test API endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"

def main():
    print("Testing API endpoints...")
    
    # Test health check
    print("\n=== Health Check ===")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/health/")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test detailed health check
    print("\n=== Detailed Health Check ===")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/health/detailed")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test listings endpoint
    print("\n=== Listings ===")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/listings/?page=1&page_size=5")
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Total: {data.get('total', 0)}")
        print(f"Items: {len(data.get('items', []))}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test valuation endpoint
    print("\n=== Valuation ===")
    try:
        payload = {
            "preco_pedido": 250000,
            "area_util_m2": 80,
            "quartos": 2,
            "casas_banho": 1,
            "concelho": "Porto",
            "freguesia": "Bonfim"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/valuation/", json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test scoring endpoint
    print("\n=== Scoring ===")
    try:
        payload = {
            "preco_pedido": 250000,
            "area_util_m2": 80,
            "quartos": 2,
            "casas_banho": 1,
            "concelho": "Porto"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/scoring/", json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {resp.json()}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nAPI test complete")

if __name__ == "__main__":
    main()
