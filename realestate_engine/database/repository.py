"""Database repository with ACID transactions for Real Estate Opportunity Engine."""
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, UTC
from sqlalchemy import create_engine, select, update, delete, func
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.pool import StaticPool
from loguru import logger

from realestate_engine.database.models import (
    Base, RawListing, CleanListing, Valuation, Score, PriceHistory,
    Notification, ConfigEntry, JobExecutionLog, init_db, get_engine, get_session_factory
)
from realestate_engine.utils.config import config


@contextmanager
def transaction_scope(session: Session) -> Generator[Session, None, None]:
    """Context manager for ACID transactions with automatic rollback."""
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise
    finally:
        session.close()


class DatabaseRepository:
    """Repository pattern for database operations with ACID transactions."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.engine = get_engine(database_url or config.database_url)
        self.Session = get_session_factory(self.engine)
    
    def init_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables initialized")
    
    def execute_with_transaction(self, operations: List[Any]) -> None:
        """Execute multiple operations in a single ACID transaction."""
        with transaction_scope(self.Session()) as session:
            for operation in operations:
                session.execute(operation)
    
    # Raw Listings
    def create_raw_listing(self, raw: RawListing) -> RawListing:
        """Insert a raw listing."""
        with transaction_scope(self.Session()) as session:
            session.add(raw)
            return raw
    
    def create_raw_listings_batch(self, raws: List[RawListing]) -> List[RawListing]:
        """Batch insert raw listings in a single transaction."""
        with transaction_scope(self.Session()) as session:
            session.add_all(raws)
            return raws
    
    def get_raw_listings(self, portal: Optional[str] = None, limit: int = 1000, include_sample: bool = False) -> List[RawListing]:
        """Get raw listings, optionally filtered by portal.
        
        Args:
            portal: Filter by source portal
            limit: Maximum number of results
            include_sample: If False, exclude sample data (is_sample=1)
        """
        with self.Session() as session:
            query = select(RawListing)
            
            # Filter out sample data by default
            if not include_sample:
                query = query.where(RawListing.is_sample == 0)
            
            if portal:
                query = query.where(RawListing.source_portal == portal)
            query = query.limit(limit)
            return list(session.execute(query).unique().scalars().all())
    
    def get_raw_listing_by_source_id(self, source_portal: str, source_id: str) -> Optional[RawListing]:
        """Get raw listing by portal and source ID."""
        with self.Session() as session:
            result = session.execute(
                select(RawListing).where(
                    RawListing.source_portal == source_portal,
                    RawListing.source_id == source_id
                )
            ).scalar_one_or_none()
            return result
    
    def delete_sample_raw_listings(self) -> int:
        """Delete all raw listings marked as sample data (is_sample=1)."""
        with self.Session() as session:
            result = session.execute(
                delete(RawListing).where(RawListing.is_sample == 1)
            )
            session.commit()
            count = result.rowcount
            logger.info(f"Deleted {count} sample raw listings")
            return count
    
    # Clean Listings
    def create_clean_listing(self, clean: CleanListing) -> CleanListing:
        """Insert a clean listing."""
        with transaction_scope(self.Session()) as session:
            session.add(clean)
            return clean
    
    def create_clean_listings_batch(self, cleans: List[CleanListing]) -> List[CleanListing]:
        """Batch insert clean listings."""
        with transaction_scope(self.Session()) as session:
            session.add_all(cleans)
            return cleans
    
    def get_clean_listings(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        preco_min: Optional[float] = None,
        preco_max: Optional[float] = None,
        area_min: Optional[float] = None,
        area_max: Optional[float] = None,
        quartos_min: Optional[int] = None,
        quartos_max: Optional[int] = None,
        include_sample: bool = False
    ) -> List[CleanListing]:
        """Get clean listings with optional filters and SQL-level pagination.
        
        Args:
            filters: Dictionary of field filters (exact match)
            limit: Maximum number of results
            offset: SQL offset for pagination
            preco_min: Minimum price filter
            preco_max: Maximum price filter
            area_min: Minimum area filter
            area_max: Maximum area filter
            quartos_min: Minimum bedrooms filter
            quartos_max: Maximum bedrooms filter
            include_sample: If False, exclude sample data (is_sample=1)
        """
        with self.Session() as session:
            query = select(CleanListing).options(joinedload(CleanListing.valuations))
            
            # Filter out sample data by default
            if not include_sample:
                query = query.where(CleanListing.is_sample == 0)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(CleanListing, key) and value is not None:
                        query = query.where(getattr(CleanListing, key) == value)
            
            # Numeric range filters
            if preco_min is not None:
                query = query.where(CleanListing.preco_pedido >= preco_min)
            if preco_max is not None:
                query = query.where(CleanListing.preco_pedido <= preco_max)
            if area_min is not None:
                query = query.where(CleanListing.area_util_m2 >= area_min)
            if area_max is not None:
                query = query.where(CleanListing.area_util_m2 <= area_max)
            if quartos_min is not None:
                query = query.where(CleanListing.quartos >= quartos_min)
            if quartos_max is not None:
                query = query.where(CleanListing.quartos <= quartos_max)
            
            query = query.offset(offset).limit(limit)
            return list(session.execute(query).unique().scalars().all())
    
    def get_clean_listing_by_id(self, listing_id: str) -> Optional[CleanListing]:
        """Get a clean listing by its UUID."""
        with self.Session() as session:
            return session.execute(
                select(CleanListing).options(joinedload(CleanListing.valuations))
                .where(CleanListing.id == listing_id)
            ).scalar_one_or_none()

    def get_clean_listing_by_source(self, portal: str, source_id: str) -> Optional[CleanListing]:
        """Get a clean listing by its source portal and ID."""
        with self.Session() as session:
            return session.query(CleanListing).options(joinedload(CleanListing.valuations)).filter(
                CleanListing.source_portal == portal,
                CleanListing.source_id == source_id
            ).first()

    def get_raw_listing_by_source(self, portal: str, source_id: str) -> Optional[RawListing]:
        """Get the newest raw listing by portal and source ID."""
        with self.Session() as session:
            return session.execute(
                select(RawListing)
                .where(
                    RawListing.source_portal == portal,
                    RawListing.source_id == source_id,
                )
                .order_by(RawListing.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()

    def get_raw_listings_since(self, since: Optional[datetime], limit: int = 1000, include_sample: bool = False) -> List[RawListing]:
        """Get raw listings created after a given timestamp."""
        with self.Session() as session:
            query = select(RawListing)
            if not include_sample:
                query = query.where(RawListing.is_sample == 0)
            if since is not None:
                query = query.where(RawListing.created_at > since)
            query = query.order_by(RawListing.created_at.asc()).limit(limit)
            return list(session.execute(query).scalars().all())
    
    def get_unprocessed_raw_listings(self, limit: int = 1000, include_sample: bool = False) -> List[RawListing]:
        """Get raw listings that don't have a corresponding clean listing (backlog processing)."""
        with self.Session() as session:
            # Use LEFT JOIN to find raw_listings without matching clean_listings
            from sqlalchemy import and_
            
            # Subquery to get all (source_portal, source_id) from clean_listings
            clean_subq = session.query(
                CleanListing.source_portal,
                CleanListing.source_id
            ).subquery()
            
            # LEFT JOIN with clean_listings and filter where clean_listings.id IS NULL
            query = select(RawListing).outerjoin(
                clean_subq,
                and_(
                    RawListing.source_portal == clean_subq.c.source_portal,
                    RawListing.source_id == clean_subq.c.source_id
                )
            ).where(clean_subq.c.source_id.is_(None))
            
            if not include_sample:
                query = query.where(RawListing.is_sample == 0)
            
            query = query.order_by(RawListing.created_at.asc()).limit(limit)
            return list(session.execute(query).scalars().all())

    def get_last_successful_job_execution(self, job_name: str) -> Optional[JobExecutionLog]:
        """Get the most recent successful execution of a job."""
        with self.Session() as session:
            return session.execute(
                select(JobExecutionLog)
                .where(
                    JobExecutionLog.job_name == job_name,
                    JobExecutionLog.status == "success",
                )
                .order_by(JobExecutionLog.finished_at.desc())
                .limit(1)
            ).scalar_one_or_none()
    
    def update_clean_listing(self, listing_id: str, updates: Dict[str, Any]) -> bool:
        """Update clean listing fields."""
        with self.Session() as session:
            # Filter updates to only include valid columns for CleanListing
            valid_keys = {c.name for c in CleanListing.__table__.columns}
            filtered_updates = {k: v for k, v in updates.items() if k in valid_keys}
            
            if not filtered_updates:
                return False
                
            result = session.execute(
                update(CleanListing)
                .where(CleanListing.id == listing_id)
                .values(**filtered_updates)
            )
            session.commit()
            return result.rowcount > 0
    
    def delete_sample_clean_listings(self) -> int:
        """Delete all clean listings marked as sample data (is_sample=1)."""
        with self.Session() as session:
            result = session.execute(
                delete(CleanListing).where(CleanListing.is_sample == 1)
            )
            session.commit()
            count = result.rowcount
            logger.info(f"Deleted {count} sample clean listings")
            return count

    def assert_no_sample_data(self) -> None:
        """Raise RuntimeError if any raw/clean listing is flagged as sample."""
        with self.Session() as session:
            raw_flagged = session.execute(
                select(func.count()).select_from(RawListing).where(RawListing.is_sample == 1)
            ).scalar_one()
            clean_flagged = session.execute(
                select(func.count()).select_from(CleanListing).where(CleanListing.is_sample == 1)
            ).scalar_one()

        if raw_flagged or clean_flagged:
            raise RuntimeError(
                "Fake data detected: remove records with is_sample=1 before running the pipeline"
            )
    
    # Watchlist
    def add_to_watchlist(self, listing_id: str, user_id: str = "default", notes: str = "", tags: List[str] = None) -> bool:
        """Add a listing to the watchlist."""
        from realestate_engine.database.models import Watchlist
        from sqlalchemy import select
        
        with self.Session() as session:
            # Check if already in watchlist
            existing = session.execute(
                select(Watchlist).where(
                    Watchlist.listing_id == listing_id,
                    Watchlist.user_id == user_id
                )
            ).scalar_one_or_none()
            
            if existing:
                return False  # Already in watchlist
            
            watchlist_item = Watchlist(
                listing_id=listing_id,
                user_id=user_id,
                notes=notes,
                tags=tags or []
            )
            session.add(watchlist_item)
            session.commit()
            logger.info(f"Added listing {listing_id} to watchlist for user {user_id}")
            return True
    
    def remove_from_watchlist(self, listing_id: str, user_id: str = "default") -> bool:
        """Remove a listing from the watchlist."""
        from realestate_engine.database.models import Watchlist
        
        with self.Session() as session:
            result = session.execute(
                delete(Watchlist).where(
                    Watchlist.listing_id == listing_id,
                    Watchlist.user_id == user_id
                )
            )
            session.commit()
            count = result.rowcount
            logger.info(f"Removed listing {listing_id} from watchlist for user {user_id}")
            return count > 0
    
    def get_watchlist(self, user_id: str = "default") -> List[CleanListing]:
        """Get all listings in the user's watchlist."""
        from realestate_engine.database.models import Watchlist
        from sqlalchemy.orm import joinedload
        
        with self.Session() as session:
            watchlist_items = session.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
            ).scalars().all()
            
            listing_ids = [item.listing_id for item in watchlist_items]
            
            if not listing_ids:
                return []
            
            # Get the actual listings
            listings = session.execute(
                select(CleanListing).options(joinedload(CleanListing.valuations))
                .where(CleanListing.id.in_(listing_ids))
                .where(CleanListing.is_sample == 0)
            ).unique().scalars().all()
            
            return list(listings)
    
    def is_in_watchlist(self, listing_id: str, user_id: str = "default") -> bool:
        """Check if a listing is in the watchlist."""
        from realestate_engine.database.models import Watchlist
        
        with self.Session() as session:
            existing = session.execute(
                select(Watchlist).where(
                    Watchlist.listing_id == listing_id,
                    Watchlist.user_id == user_id
                )
            ).scalar_one_or_none()
            
            return existing is not None
    
    # Valuations
    def create_valuation(self, valuation: Valuation) -> Valuation:
        """Insert a valuation."""
        with transaction_scope(self.Session()) as session:
            session.add(valuation)
            return valuation
    
    def create_valuations_batch(self, valuations: List[Valuation]) -> List[Valuation]:
        """Batch insert valuations."""
        with transaction_scope(self.Session()) as session:
            session.add_all(valuations)
            return valuations
    
    def get_valuation_by_listing(self, listing_id: str) -> Optional[Valuation]:
        """Get latest valuation for a listing."""
        with self.Session() as session:
            return session.execute(
                select(Valuation).where(Valuation.listing_id == listing_id)
                .order_by(Valuation.created_at.desc())
            ).scalar_one_or_none()
    
    def get_valuations_without_scores(self, limit: int = 1000) -> List[Valuation]:
        """Get valuations that don't have scores yet."""
        with self.Session() as session:
            from sqlalchemy.orm import aliased
            scored = select(Score.listing_id).subquery()
            query = select(Valuation).where(
                ~Valuation.listing_id.in_(scored)
            ).limit(limit)
            return list(session.execute(query).scalars().all())
    
    # Scores
    def create_score(self, score: Score) -> Score:
        """Insert a score."""
        with transaction_scope(self.Session()) as session:
            session.add(score)
            return score
    
    def create_scores_batch(self, scores: List[Score]) -> List[Score]:
        """Batch insert scores."""
        with transaction_scope(self.Session()) as session:
            session.add_all(scores)
            return scores
    
    def get_top_scores(self, min_score: float = 8.0, limit: int = 50, include_sample: bool = False) -> List[Score]:
        """Get top scoring listings from existing clean listings only.
        
        Args:
            min_score: Minimum score threshold
            limit: Maximum number of results
            include_sample: If False, exclude sample data (is_sample=1)
        """
        from sqlalchemy.orm import joinedload
        with self.Session() as session:
            query = select(Score).options(
                joinedload(Score.listing).joinedload(CleanListing.valuations)
            ).join(Score.listing).where(Score.score_total >= min_score)
            
            # Filter out sample data by default
            if not include_sample:
                query = query.where(CleanListing.is_sample == 0)
            
            query = query.order_by(Score.score_total.desc()).limit(limit)
            return list(session.execute(query).unique().scalars().all())
    
    def get_score_by_listing(self, listing_id: str) -> Optional[Score]:
        """Get score for a listing."""
        with self.Session() as session:
            return session.execute(
                select(Score).where(Score.listing_id == listing_id)
                .order_by(Score.created_at.desc())
            ).scalar_one_or_none()
    
    # Notifications
    def create_notification(self, notification: Notification) -> Notification:
        """Insert a notification record."""
        with transaction_scope(self.Session()) as session:
            session.add(notification)
            return notification
    
    def update_notification_status(self, notification_id: str, status: str, error: Optional[str] = None) -> bool:
        """Update notification status."""
        with transaction_scope(self.Session()) as session:
            updates = {"status": status}
            if error:
                updates["error_message"] = error
            if status == "sent":
                updates["sent_at"] = datetime.now(UTC)
            stmt = update(Notification).where(Notification.id == notification_id).values(**updates)
            session.execute(stmt)
            return True
    
    def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """Get notifications pending send."""
        with self.Session() as session:
            return list(session.execute(
                select(Notification).where(Notification.status == "pending")
                .limit(limit)
            ).scalars().all())
    
    def get_notifications_sent_today(self) -> int:
        """Count notifications sent today."""
        with self.Session() as session:
            from datetime import date
            today = date.today().isoformat()
            return session.execute(
                select(func.count(Notification.id)).where(
                    Notification.status == "sent",
                    Notification.sent_at >= today
                )
            ).scalar() or 0

    def get_notifications_by_listing(self, listing_id: str) -> List[Notification]:
        """Get all notifications for a specific listing."""
        with self.Session() as session:
            return list(session.execute(
                select(Notification).where(Notification.listing_id == listing_id)
                .order_by(Notification.sent_at.desc())
            ).scalars().all())
    
    # Price History
    def add_price_history(self, price_history: PriceHistory) -> PriceHistory:
        """Insert price history entry."""
        with transaction_scope(self.Session()) as session:
            session.add(price_history)
            return price_history
    
    def get_price_history(self, listing_id: str) -> List[PriceHistory]:
        """Get price history for a listing."""
        with self.Session() as session:
            return list(session.execute(
                select(PriceHistory).where(PriceHistory.listing_id == listing_id)
                .order_by(PriceHistory.data.desc())
            ).scalars().all())
    
    # Config
    def get_config(self, key: str) -> Optional[Any]:
        """Get config value by key."""
        with self.Session() as session:
            entry = session.execute(
                select(ConfigEntry).where(ConfigEntry.key == key)
            ).scalar_one_or_none()
            return entry.value if entry else None
    
    def set_config(self, key: str, value: Any) -> ConfigEntry:
        """Set config value."""
        with transaction_scope(self.Session()) as session:
            entry = ConfigEntry(key=key, value=value)
            session.merge(entry)
            return entry
    
    # Job Execution Log
    def log_job_start(self, job_name: str) -> JobExecutionLog:
        """Log job start."""
        with transaction_scope(self.Session()) as session:
            log = JobExecutionLog(job_name=job_name, status="running")
            session.add(log)
            # Need to flush to get ID, or commit.
            # with session.begin() will commit at end.
            # If I need log.id now, I should use session.flush()
            session.flush()
            # session.refresh(log) # cannot refresh in mid-transaction easily with begin()
            # but log.id should be available after flush.
            # Wait, transaction_scope uses with session.begin(): yield session
            # So I should return log and hope its ID is populated.
            return log
    
    def log_job_end(self, log_id: int, status: str, error: Optional[str] = None, records: int = 0) -> bool:
        """Log job end."""
        with transaction_scope(self.Session()) as session:
            updates = {
                "finished_at": datetime.now(UTC),
                "status": status,
                "records_processed": records
            }
            if error:
                updates["error_message"] = error
            stmt = update(JobExecutionLog).where(JobExecutionLog.id == log_id).values(**updates)
            session.execute(stmt)
            return True
    
    def get_last_job_execution(self, job_name: str) -> Optional[JobExecutionLog]:
        """Get last execution of a job."""
        with self.Session() as session:
            return session.execute(
                select(JobExecutionLog).where(JobExecutionLog.job_name == job_name)
                .order_by(JobExecutionLog.started_at.desc())
            ).scalar_one_or_none()
    
    def get_recent_job_executions(self, job_name: str, limit: int = 10) -> List[JobExecutionLog]:
        """Get recent executions of a job."""
        with self.Session() as session:
            return list(session.execute(
                select(JobExecutionLog).where(JobExecutionLog.job_name == job_name)
                .order_by(JobExecutionLog.started_at.desc())
                .limit(limit)
            ).scalars().all())

    # ── Methods required by Deduplicator & Notification Engine ──────────
    def get_all_fingerprints(self) -> set:
        """Get all existing listing fingerprints for deduplication.
        Generates fingerprints from existing CleanListings in the DB."""
        from realestate_engine.etl.deduplicator import Deduplicator
        with self.Session() as session:
            listings = session.execute(select(CleanListing)).scalars().all()
            fingerprints = set()
            for listing in listings:
                fp = Deduplicator.generate_fingerprint({
                    "freguesia": listing.freguesia,
                    "tipologia": listing.tipologia,
                    "area_util_m2": listing.area_util_m2,
                    "preco_pedido": listing.preco_pedido,
                    "source_id": listing.source_id,
                })
                fingerprints.add(fp)
            return fingerprints

    def get_total_clean_listings_count(self) -> int:
        """Get total number of clean listings."""
        with self.Session() as session:
            return session.execute(
                select(func.count(CleanListing.id))
            ).scalar() or 0

    def get_new_listings_today_count(self) -> int:
        """Get number of listings scraped today."""
        from datetime import date
        with self.Session() as session:
            today = date.today().isoformat()
            return session.execute(
                select(func.count(CleanListing.id)).where(
                    CleanListing.scrape_timestamp >= today
                )
            ).scalar() or 0

    def get_notifications_for_listing(self, listing_id: str) -> List[Notification]:
        """Get all notifications for a specific listing."""
        with self.Session() as session:
            return list(session.execute(
                select(Notification).where(Notification.listing_id == listing_id)
                .order_by(Notification.created_at.desc())
            ).scalars().all())

