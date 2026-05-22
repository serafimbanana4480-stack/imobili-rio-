"""Maintenance job for system cleanup and proxy refresh."""
from loguru import logger
from realestate_engine.scraping.proxy_manager import ProxyManager
from realestate_engine.utils.decorators import async_retry

class MaintenanceJob:
    """Handles system maintenance tasks."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
    
    @async_retry(max_attempts=3, delay=60)
    async def run(self) -> int:
        """Run maintenance tasks."""
        logger.info("Starting maintenance job")
        
        # Refresh proxies
        await self.proxy_manager.refresh_proxies()
        
        logger.info("Maintenance job completed")
        return 1

    async def model_retrain(self):
        """Retrain valuation models."""
        logger.info("Starting model retrain job")
        from realestate_engine.valuation.valuation_engine import ValuationEngine
        engine = ValuationEngine()
        count = engine.retrain()
        logger.info(f"Models retrained successfully using {count} samples")
        return count

    async def db_cleanup(self):
        """Cleanup old data (raw listings older than 30 days)."""
        logger.info("Starting DB cleanup job")
        from realestate_engine.database.models import RawListing
        from sqlalchemy import delete
        from datetime import datetime, timedelta, timezone
        
        limit_date = datetime.now(timezone.utc) - timedelta(days=30)
        with self.proxy_manager.repo.Session() as session:
            stmt = delete(RawListing).where(RawListing.created_at < limit_date)
            result = session.execute(stmt)
            session.commit()
            count = result.rowcount
            
        logger.info(f"DB cleanup completed: removed {count} old raw listings")
        return count

    async def ine_refresh(self):
        """Refresh INE data (simulation of API fetch)."""
        logger.info("Starting INE data refresh job")
        from realestate_engine.database.models import INEData
        from datetime import datetime
        
        # This would call the real INE API: https://www.ine.pt/ine/api_json
        # Here we refresh our local data with slightly updated simulated values
        regions = ["Porto", "Cedofeita", "Paranhos", "Bonfim", "Foz do Douro"]
        
        with self.proxy_manager.repo.Session() as session:
            for region in regions:
                data = INEData(
                    concelho=region,
                    preco_mediano_m2=2500 + (len(region) * 100), # Deterministic mock
                    ano=2026,
                    trimestre=1,
                    fetched_at=datetime.now(timezone.utc)
                )
                session.add(data)
            session.commit()
            
        logger.info("INE data refreshed successfully")
        return len(regions)
