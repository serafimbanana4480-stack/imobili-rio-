"""Diagnose why clean listings count is not updating."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import RawListing, CleanListing
from sqlalchemy import select, func


def main() -> int:
    print("=" * 60)
    print("DIAGNÓSTICO: Por que clean listings não atualiza?")
    print("=" * 60)
    print()
    
    repo = DatabaseRepository()
    
    with repo.Session() as session:
        # 1. Count raw_listings
        raw_count = session.execute(select(func.count(RawListing.id))).scalar()
        print(f"📊 Total raw_listings: {raw_count:,}")
        
        # 2. Count clean_listings
        clean_count = session.execute(select(func.count(CleanListing.id))).scalar()
        print(f"📊 Total clean_listings: {clean_count:,}")
        
        # 3. Check latest raw listings
        latest_raw = session.execute(
            select(RawListing).order_by(RawListing.scrape_timestamp.desc()).limit(5)
        ).scalars().all()
        
        print()
        print(f"📋 Últimos 5 raw_listings:")
        for raw in latest_raw:
            print(f"  • {raw.source_portal} / {raw.source_id} - {raw.scrape_timestamp}")
        
        # 4. Check latest clean listings
        latest_clean = session.execute(
            select(CleanListing).order_by(CleanListing.scrape_timestamp.desc()).limit(5)
        ).scalars().all()
        
        print()
        print(f"📋 Últimos 5 clean_listings:")
        for clean in latest_clean:
            print(f"  • {clean.source_portal} / {clean.source_id} - {clean.scrape_timestamp}")
        
        # 5. Check raw_listings that are NOT in clean_listings (unprocessed)
        print()
        print(f"🔍 Verificando raw_listings não processados...")
        
        # Simplified check: compare counts
        # If raw_listings > clean_listings, there are unprocessed items
        unprocessed_estimate = raw_count - clean_count
        print(f"  • Estimativa de não processados: {unprocessed_estimate:,} (raw - clean)")
        
        # Check if latest raw is in clean_listings
        if latest_raw:
            latest = latest_raw[0]
            in_clean = session.execute(
                select(func.count(CleanListing.id)).where(
                    CleanListing.source_portal == latest.source_portal,
                    CleanListing.source_id == latest.source_id
                )
            ).scalar()
            print(f"  • Último raw_listing ({latest.source_portal}/{latest.source_id}) está em clean_listings: {'SIM' if in_clean > 0 else 'NÃO'}")
        
        # 6. Check if raw_listings are being added recently
        print()
        print(f"🕐 Verificando scraping recente...")
        
        from datetime import datetime, timedelta, UTC
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        
        recent_raw = session.execute(
            select(func.count(RawListing.id)).where(
                RawListing.scrape_timestamp >= one_hour_ago
            )
        ).scalar()
        
        print(f"  • Raw_listings nas últimas 1h: {recent_raw:,}")
        
        if recent_raw == 0:
            print(f"  ⚠️  NENHUM scraping recente! O scraping pode não estar a funcionar.")
        
        # 7. Check if ETL is running
        print()
        print(f"🕐 Verificando ETL recente...")
        
        recent_clean = session.execute(
            select(func.count(CleanListing.id)).where(
                CleanListing.scrape_timestamp >= one_hour_ago
            )
        ).scalar()
        
        print(f"  • Clean_listings criadas nas últimas 1h: {recent_clean:,}")
        
        if recent_clean == 0 and recent_raw > 0:
            print(f"  ⚠️  Há raw_listings recentes mas NENHUM clean_listing!")
            print(f"  ⚠️  O ETL pode não estar a funcionar.")
        
        # 8. Diagnosis
        print()
        print("=" * 60)
        print("DIAGNÓSTICO:")
        print("=" * 60)
        
        if recent_raw == 0:
            print("❌ PROBLEMA: O scraping não está a adicionar novos dados.")
            print("   → Verifica se os spiders estão a funcionar")
            print("   → Verifica se há erros nos logs de scraping")
        elif unprocessed_estimate > 0:
            print(f"⚠️  PROBLEMA: Há ~{unprocessed_estimate:,} raw_listings não processados.")
            print("   → O ETL pode não estar a funcionar")
            print("   → Executa o ETL manualmente: python scripts/debug/_run_etl_full.py")
        elif recent_clean == 0:
            print("⚠️  PROBLEMA: O ETL não está a criar novos clean_listings.")
            print("   → Executa o ETL manualmente: python scripts/debug/_run_etl_full.py")
        else:
            print("✅ Tudo parece normal. O count pode estar correto.")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
