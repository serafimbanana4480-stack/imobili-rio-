"""Listing Janitor for database maintenance: deduplication and availability checking."""
import asyncio
import httpx
from typing import List, Dict, Tuple
from loguru import logger
from sqlalchemy import select, update
from datetime import datetime, timezone

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing
from realestate_engine.etl.fuzzy_deduplicator import FuzzyDeduplicator

class ListingJanitor:
    """Maintenance service for cleaning duplicates and dead listings."""

    def __init__(self, repo: DatabaseRepository = None):
        self.repo = repo or DatabaseRepository()
        self.deduplicator = FuzzyDeduplicator()

    async def run_deduplication(self) -> int:
        """Find and mark duplicate listings in the database."""
        logger.info("Starting database deduplication check...")
        
        # Get all active, non-duplicate listings
        listings = self.repo.get_clean_listings(limit=100000)
        if not listings:
            return 0

        # Convert to format expected by deduplicator
        pool = []
        for l in listings:
            pool.append({
                "id": l.id,
                "source_portal": l.source_portal,
                "source_id": l.source_id,
                "titulo": l.titulo,
                "preco_pedido": l.preco_pedido,
                "area_util_m2": l.area_util_m2,
                "tipologia": l.tipologia,
                "freguesia": l.freguesia,
                "concelho": l.concelho,
                "lat": l.lat,
                "lon": l.lon
            })

        duplicates = self.deduplicator.find_duplicates(pool)
        if not duplicates:
            logger.info("No duplicates found.")
            return 0

        marked_count = 0
        with self.repo.Session() as session:
            for original_id, duplicate_ids in duplicates.items():
                for dup_id in duplicate_ids:
                    session.execute(
                        update(CleanListing)
                        .where(CleanListing.id == dup_id)
                        .values(is_duplicate=1, duplicate_of_id=original_id)
                    )
                    marked_count += 1
            session.commit()

        logger.info(f"Deduplication complete. Marked {marked_count} listings as duplicates.")
        return marked_count

    async def check_availability(self, batch_size: int = 50) -> Dict[str, int]:
        """Check if listings are still available on the source portals."""
        logger.info("Starting availability check for active listings...")
        
        # Get oldest active listings to check
        with self.repo.Session() as session:
            query = select(CleanListing).where(
                CleanListing.is_active == 1,
                CleanListing.is_duplicate == 0
            ).order_by(CleanListing.updated_at.asc()).limit(batch_size)
            listings = session.execute(query).scalars().all()

        if not listings:
            return {"checked": 0, "removed": 0}

        removed_count = 0
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            tasks = [self._is_listing_gone(client, l) for l in listings]
            results = await asyncio.gather(*tasks)

        with self.repo.Session() as session:
            for listing, is_gone in zip(listings, results):
                if is_gone:
                    session.execute(
                        update(CleanListing)
                        .where(CleanListing.id == listing.id)
                        .values(is_active=0)
                    )
                    removed_count += 1
                else:
                    # Update timestamp even if active so we don't re-check immediately
                    session.execute(
                        update(CleanListing)
                        .where(CleanListing.id == listing.id)
                        .values(updated_at=datetime.now(timezone.utc))
                    )
            session.commit()

        logger.info(f"Availability check complete. Checked {len(listings)}, marked {removed_count} as inactive.")
        return {"checked": len(listings), "removed": removed_count}

    async def _is_listing_gone(self, client: httpx.AsyncClient, listing: CleanListing) -> bool:
        """Heuristic check if a listing URL is dead or says 'not found'."""
        try:
            resp = await client.get(listing.source_url)
            
            # Direct dead signals
            if resp.status_code == 404:
                return True
            
            # Portal-specific "gone" markers in HTML
            text = resp.text.lower()
            gone_markers = [
                "imóvel indisponível",
                "página não encontrada",
                "anúncio removido",
                "já não se encontra disponível",
                "venda concluída",
                "item not found",
                "listing removed"
            ]
            
            if any(marker in text for marker in gone_markers):
                return True
                
            return False
        except Exception as e:
            logger.debug(f"Failed to check URL {listing.source_url}: {e}")
            # If request fails multiple times, we might assume it's gone, 
            # but for safety let's return False (active) to avoid false positives.
            return False
