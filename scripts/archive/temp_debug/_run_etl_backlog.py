"""Run ETL with force_full=True to process unprocessed backlog."""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.etl.pipeline_etl import PipelineETL


async def main() -> int:
    print("=" * 60)
    print("ETL BACKLOG PROCESSING")
    print("=" * 60)
    print("Processing all unprocessed raw_listings...")
    print()
    
    etl = PipelineETL()
    
    # Process in batches of 1000 to avoid memory issues
    batch_size = 1000
    total_processed = 0
    batch_num = 0
    
    while True:
        batch_num += 1
        print(f"\n🔄 Batch {batch_num} (max {batch_size} listings)...")
        
        count = await etl.run(batch_size=batch_size, force_full=True)
        
        if count == 0:
            print("✅ No more unprocessed raw_listings")
            break
        
        total_processed += count
        print(f"✅ Processed {count} listings in this batch")
        print(f"📊 Total processed so far: {total_processed:,}")
        
        # Safety limit to prevent infinite loop
        if batch_num >= 50:  # Max 50 batches = 50,000 listings
            print("⚠️  Reached safety limit of 50 batches")
            break
    
    print()
    print("=" * 60)
    print(f"BACKLOG PROCESSING COMPLETE")
    print(f"Total processed: {total_processed:,}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
