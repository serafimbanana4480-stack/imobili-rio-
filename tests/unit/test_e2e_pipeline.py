"""End-to-End Pipeline Test: Scrape → ETL → Valuation → Scoring → API"""
import sys
import os

# Add the project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import with full module path
from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.etl.pipeline_etl import PipelineETL
import requests

def test_e2e_pipeline():
    """Test complete pipeline from scrape to API."""
    print("=" * 60)
    print("END-TO-END PIPELINE TEST")
    print("=" * 60)
    
    # Initialize
    repo = DatabaseRepository()
    spider = CasaSapoDirectSpider()
    etl = PipelineETL(repo)
    valuation_engine = ValuationEngine(repo)
    scoring_engine = ScoringEngine(repo)
    
    # Step 1: Scrape
    print("\n[Step 1] Scraping Casa Sapo Direct...")
    try:
        import asyncio
        raw_listings = asyncio.run(spider.run(max_pages=1))
        print(f"✓ Scraped {len(raw_listings)} raw listings")
    except Exception as e:
        raise AssertionError(f"Scraping failed: {e}") from e
    
    # Step 2: Save raw listings
    print("\n[Step 2] Saving raw listings...")
    try:
        from realestate_engine.database.models import RawListing
        from datetime import datetime, timezone
        import json
        
        # Converter dicionários para objetos RawListing
        raw_objects = []
        for listing_dict in raw_listings:
            raw = RawListing(
                source_portal=listing_dict.get("source_portal", "casa_sapo"),
                source_id=listing_dict.get("source_id", ""),
                source_url=listing_dict.get("source_url", ""),
                scrape_timestamp=datetime.now(timezone.utc).isoformat(),
                raw_data=listing_dict,
                is_sample=1  # Mark as sample for testing
            )
            raw_objects.append(raw)
        
        repo.create_raw_listings_batch(raw_objects)
        print(f"✓ Saved {len(raw_objects)} raw listings")
    except Exception as e:
        raise AssertionError(f"Saving raw listings failed: {e}") from e
    
    # Step 3: Run ETL pipeline
    print("\n[Step 3] Running ETL pipeline...")
    try:
        processed = etl.run(batch_size=100)
        print(f"✓ ETL processed {processed} listings")
    except Exception as e:
        raise AssertionError(f"ETL failed: {e}") from e
    
    # Step 4: Run valuation
    print("\n[Step 4] Running valuation...")
    try:
        valued = valuation_engine.valuate_batch(batch_size=10)
        print(f"✓ Valued {valued} listings")
    except Exception as e:
        raise AssertionError(f"Valuation failed: {e}") from e
    
    # Step 5: Run scoring
    print("\n[Step 5] Running scoring...")
    try:
        scored = scoring_engine.score_batch(batch_size=10)
        print(f"✓ Scored {scored} listings")
    except Exception as e:
        raise AssertionError(f"Scoring failed: {e}") from e
    
    # Step 6: Verify API
    print("\n[Step 6] Verifying API endpoints...")
    try:
        # Health check
        resp = requests.get("http://localhost:8000/api/v1/health/")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        print("✓ Health check OK")
        
        # Listings endpoint
        resp = requests.get("http://localhost:8000/api/v1/listings/?page=1&page_size=5")
        assert resp.status_code == 200, f"Listings failed: {resp.status_code}"
        data = resp.json()
        print(f"✓ Listings endpoint OK ({data['total']} listings)")
        
        # Valuation endpoint
        payload = {
            "preco_pedido": 250000,
            "area_util_m2": 80,
            "quartos": 2,
            "casas_banho": 1,
            "concelho": "Porto",
            "freguesia": "Bonfim"
        }
        resp = requests.post("http://localhost:8000/api/v1/valuation/", json=payload)
        assert resp.status_code == 200, f"Valuation failed: {resp.status_code}"
        print("✓ Valuation endpoint OK")
        
        # Scoring endpoint
        resp = requests.post("http://localhost:8000/api/v1/scoring/", json=payload)
        assert resp.status_code == 200, f"Scoring failed: {resp.status_code}"
        print("✓ Scoring endpoint OK")
        
    except Exception as e:
        raise AssertionError(f"API verification failed: {e}") from e
    
    print("\n" + "=" * 60)
    print("END-TO-END PIPELINE TEST: ✅ PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_e2e_pipeline()
    sys.exit(0)
