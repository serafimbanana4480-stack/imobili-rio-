"""Test full ETL pipeline with Casa Sapo Direct data."""
import asyncio
import sys
sys.path.insert(0, '.')

from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.database.repository import DatabaseRepository

async def main():
    print("Testing ETL Pipeline with Casa Sapo Direct data...")
    
    # Step 1: Scrape data with Casa Sapo Direct
    print("\n=== Step 1: Scraping ===")
    spider_manager = SpiderManager()
    raw_results = await spider_manager.run_spider("casa_sapo", max_pages=1)
    print(f"Scraped {len(raw_results)} raw listings")
    
    if not raw_results:
        print("No data scraped, cannot continue ETL test")
        return
    
    # Step 2: Check raw listings in DB
    print("\n=== Step 2: Check Raw Listings ===")
    repo = DatabaseRepository()
    raw_listings = repo.get_raw_listings(limit=10)
    print(f"Raw listings in DB: {len(raw_listings)}")
    
    if raw_listings:
        print(f"Sample raw listing: {raw_listings[0].source_id}")
    
    # Step 3: Run normalization
    print("\n=== Step 3: Normalization ===")
    from realestate_engine.etl.normalizer import Normalizer
    
    # Get raw listings and normalize
    raw_listings = repo.get_raw_listings(limit=50)
    normalized = []
    for raw in raw_listings:
        try:
            clean = Normalizer.normalize(raw.raw_data, raw.source_portal)
            # Restore source_id/source_url from raw listing
            if not clean.get("source_id") and raw.source_id:
                clean["source_id"] = raw.source_id
            if not clean.get("source_url") and raw.source_url:
                clean["source_url"] = raw.source_url
            if clean.get("preco_pedido") and clean.get("area_util_m2"):
                normalized.append(clean)
        except Exception as e:
            print(f"Error normalizing {raw.source_id}: {e}")
    
    print(f"Normalized {len(normalized)} listings")
    
    # Step 4: Save clean listings
    print("\n=== Step 4: Saving Clean Listings ===")
    if normalized:
        from realestate_engine.database.models import CleanListing
        from datetime import datetime, timezone
        
        clean_listings = []
        for data in normalized:
            clean = CleanListing(
                source_portal=data.get("source_portal", "unknown"),
                source_id=data.get("source_id", ""),
                source_url=data.get("source_url", ""),
                scrape_timestamp=data.get("scrape_timestamp", datetime.now(timezone.utc).isoformat()),
                titulo=data.get("titulo", ""),
                descricao=data.get("descricao", ""),
                preco_pedido=data.get("preco_pedido", 0),
                area_util_m2=data.get("area_util_m2", 0),
                quartos=data.get("quartos", 0),
                casas_banho=data.get("casas_banho"),
                morada_raw=data.get("morada_raw", ""),
                freguesia=data.get("freguesia", ""),
                concelho=data.get("concelho", ""),
                distrito=data.get("distrito", ""),
                lat=data.get("lat"),
                lon=data.get("lon"),
                estado=data.get("estado", ""),
                ano_construcao=data.get("ano_construcao"),
                cert_energetico=data.get("cert_energetico", ""),
                tipologia=data.get("tipologia", ""),
                preco_por_m2=data.get("preco_por_m2"),
            )
            clean_listings.append(clean)
        
        repo.create_clean_listings_batch(clean_listings)
        print(f"Saved {len(clean_listings)} clean listings to DB")
    
    # Step 5: Check clean listings
    print("\n=== Step 5: Check Clean Listings ===")
    clean_listings = repo.get_clean_listings(limit=10)
    print(f"Clean listings in DB: {len(clean_listings)}")
    
    if clean_listings:
        print(f"Sample clean listing: {clean_listings[0].source_id}")
        print(f"  Price: {clean_listings[0].preco_pedido}")
        print(f"  Area: {clean_listings[0].area_util_m2}")
        print(f"  Rooms: {clean_listings[0].quartos}")
    
    print("\nETL Pipeline test complete")

if __name__ == "__main__":
    asyncio.run(main())
