"""Database repository with ACID transactions for Real Estate Opportunity Engine."""
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, timezone
from sqlalchemy import create_engine, select, update, delete, func
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.pool import StaticPool
from loguru import logger

from realestate_engine.database.models import (
    Base, RawListing, CleanListing, Valuation, Score, PriceHistory,
    Notification, ConfigEntry, JobExecutionLog, FailedRecord, ModelVersion, WeightChangeAudit,
    init_db, get_engine, get_session_factory
)
from realestate_engine.utils.config import config
from realestate_engine.cache.redis_cache import redis_cache

UTC = timezone.utc


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
    
    def get_clean_listings(self, filters: Optional[Dict[str, Any]] = None, limit: int = 1000, include_sample: bool = False) -> List[CleanListing]:
        """Get clean listings with optional filters.
        
        Args:
            filters: Dictionary of field filters
            limit: Maximum number of results
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
            query = query.limit(limit)
            return list(session.execute(query).unique().scalars().all())
    
    def get_clean_listings_for_fuzzy(self, limit: int = 5000) -> List[Dict]:
        """Return lightweight dicts with only the fields FuzzyDeduplicator needs.

        Avoids the heavy joinedload(valuations) of get_clean_listings and returns
        plain dicts so the deduplicator doesn't need ORM objects.
        """
        with self.Session() as session:
            query = (
                select(
                    CleanListing.source_portal,
                    CleanListing.source_id,
                    CleanListing.titulo,
                    CleanListing.preco_pedido,
                    CleanListing.area_util_m2,
                    CleanListing.quartos,
                    CleanListing.tipologia,
                    CleanListing.freguesia,
                    CleanListing.concelho,
                    CleanListing.lat,
                    CleanListing.lon,
                )
                .where(CleanListing.is_sample == 0)
                .limit(limit)
            )
            rows = session.execute(query).all()
            return [row._asdict() for row in rows]

    def get_clean_listings_cached(self, filters: Optional[Dict[str, Any]] = None, limit: int = 1000, include_sample: bool = False) -> List[CleanListing]:
        """Get clean listings com cache Redis."""
        cache_key = f"clean_listings:{hash(str(filters))}:{limit}:{include_sample}"
        
        cached = redis_cache.get(cache_key)
        if cached is not None:
            return cached
        
        listings = self.get_clean_listings(filters=filters, limit=limit, include_sample=include_sample)
        redis_cache.set(cache_key, listings, ttl=300)
        return listings
    
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

    def get_valuations_for_listings(self, listing_ids: List[str]) -> Dict[str, Valuation]:
        """Batch get latest valuation for multiple listings (eliminates N+1)."""
        if not listing_ids:
            return {}
        with self.Session() as session:
            from sqlalchemy import func
            subq = (
                select(Valuation.listing_id, func.max(Valuation.created_at).label("max_created"))
                .where(Valuation.listing_id.in_(listing_ids))
                .group_by(Valuation.listing_id)
                .subquery()
            )
            query = select(Valuation).join(
                subq,
                (Valuation.listing_id == subq.c.listing_id) &
                (Valuation.created_at == subq.c.max_created)
            )
            results = session.execute(query).scalars().all()
            return {v.listing_id: v for v in results}

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
                joinedload(Score.listing).options(joinedload(CleanListing.valuations))
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

    def get_scores_for_listings(self, listing_ids: List[str]) -> Dict[str, Score]:
        """Batch get scores for multiple listings (eliminates N+1)."""
        if not listing_ids:
            return {}
        with self.Session() as session:
            from sqlalchemy import func
            subq = (
                select(Score.listing_id, func.max(Score.created_at).label("max_created"))
                .where(Score.listing_id.in_(listing_ids))
                .group_by(Score.listing_id)
                .subquery()
            )
            query = select(Score).join(
                subq,
                (Score.listing_id == subq.c.listing_id) &
                (Score.created_at == subq.c.max_created)
            )
            results = session.execute(query).scalars().all()
            return {s.listing_id: s for s in results}

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
                updates["sent_at"] = datetime.now(timezone.utc)
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
                "finished_at": datetime.now(timezone.utc),
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

    # Failed Records (Dead Letter Queue)
    def create_failed_record(
        self,
        source_portal: str,
        source_id: str,
        raw_data: Dict[str, Any],
        stage: str,
        failure_reason: str,
        error_message: str,
        error_details: Optional[str] = None,
        retry_count: int = 0,
        resolved: bool = False
    ) -> int:
        """Create a failed record entry in the dead letter queue."""
        with transaction_scope(self.Session()) as session:
            failed_record = FailedRecord(
                source_portal=source_portal,
                source_id=source_id,
                raw_data=raw_data,
                stage=stage,
                failure_reason=failure_reason,
                error_message=error_message,
                error_details=error_details,
                retry_count=retry_count,
                resolved=1 if resolved else 0
            )
            session.add(failed_record)
            session.flush()
            return failed_record.id

    def get_failed_records(self, resolved: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        """Get failed records, optionally filtered by resolved status."""
        with self.Session() as session:
            query = select(FailedRecord)
            if resolved is not None:
                query = query.where(FailedRecord.resolved == (1 if resolved else 0))
            query = query.order_by(FailedRecord.created_at.desc()).limit(limit)
            results = session.execute(query).scalars().all()
            return [
                {
                    "id": r.id,
                    "source_portal": r.source_portal,
                    "source_id": r.source_id,
                    "raw_data": r.raw_data,
                    "stage": r.stage,
                    "failure_reason": r.failure_reason,
                    "error_message": r.error_message,
                    "error_details": r.error_details,
                    "retry_count": r.retry_count,
                    "resolved": r.resolved,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in results
            ]

    def update_failed_record(
        self,
        record_id: int,
        resolved: Optional[bool] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None
    ):
        """Update a failed record."""
        with transaction_scope(self.Session()) as session:
            update_data = {}
            if resolved is not None:
                update_data["resolved"] = 1 if resolved else 0
            if error_message is not None:
                update_data["error_message"] = error_message
            if retry_count is not None:
                update_data["retry_count"] = retry_count

            if update_data:
                session.execute(
                    update(FailedRecord)
                    .where(FailedRecord.id == record_id)
                    .values(**update_data)
                )

    def count_failed_records(self, resolved: Optional[bool] = None) -> int:
        """Count failed records."""
        with self.Session() as session:
            query = select(func.count(FailedRecord.id))
            if resolved is not None:
                query = query.where(FailedRecord.resolved == (1 if resolved else 0))
            return session.execute(query).scalar() or 0

    def count_failed_records_by_reason(self) -> Dict[str, int]:
        """Count failed records grouped by failure reason."""
        with self.Session() as session:
            results = session.execute(
                select(FailedRecord.failure_reason, func.count(FailedRecord.id))
                .group_by(FailedRecord.failure_reason)
            ).all()
            return {reason: count for reason, count in results}

    def count_failed_records_by_stage(self) -> Dict[str, int]:
        """Count failed records grouped by stage."""
        with self.Session() as session:
            results = session.execute(
                select(FailedRecord.stage, func.count(FailedRecord.id))
                .group_by(FailedRecord.stage)
            ).all()
            return {stage: count for stage, count in results}

    def delete_old_failed_records(self, cutoff_timestamp: float) -> int:
        """Delete failed records older than cutoff timestamp."""
        with self.Session() as session:
            result = session.execute(
                delete(FailedRecord).where(
                    FailedRecord.resolved == 1,
                    FailedRecord.created_at < datetime.fromtimestamp(cutoff_timestamp, UTC)
                )
            )
            session.commit()
            return result.rowcount

    # Model Versions
    def create_model_version(
        self,
        model_name: str,
        version: str,
        model_path: str,
        train_mae: Optional[float] = None,
        train_rmse: Optional[float] = None,
        train_r2: Optional[float] = None,
        test_mae: Optional[float] = None,
        test_rmse: Optional[float] = None,
        test_r2: Optional[float] = None,
        overfitting: bool = False,
        n_samples: Optional[int] = None,
        n_features: Optional[int] = None,
        best_iteration: Optional[int] = None,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> int:
        """Create a model version record."""
        with transaction_scope(self.Session()) as session:
            # Deactivate previous versions
            session.execute(
                update(ModelVersion)
                .where(ModelVersion.model_name == model_name)
                .values(is_active=0)
            )

            model_version = ModelVersion(
                model_name=model_name,
                version=version,
                model_path=model_path,
                train_mae=train_mae,
                train_rmse=train_rmse,
                train_r2=train_r2,
                test_mae=test_mae,
                test_rmse=test_rmse,
                test_r2=test_r2,
                overfitting=1 if overfitting else 0,
                n_samples=n_samples,
                n_features=n_features,
                best_iteration=best_iteration,
                feature_importance=feature_importance
            )
            session.add(model_version)
            session.flush()
            return model_version.id

    def get_active_model_version(self, model_name: str) -> Optional[Dict]:
        """Get the active model version for a model name."""
        with self.Session() as session:
            result = session.execute(
                select(ModelVersion)
                .where(ModelVersion.model_name == model_name, ModelVersion.is_active == 1)
                .order_by(ModelVersion.trained_at.desc())
            ).scalar_one_or_none()

            if result:
                return {
                    "id": result.id,
                    "model_name": result.model_name,
                    "version": result.version,
                    "trained_at": result.trained_at.isoformat() if result.trained_at else None,
                    "model_path": result.model_path,
                    "train_mae": result.train_mae,
                    "train_r2": result.train_r2,
                    "test_mae": result.test_mae,
                    "test_r2": result.test_r2,
                    "overfitting": result.overfitting,
                    "n_samples": result.n_samples,
                    "best_iteration": result.best_iteration,
                    "feature_importance": result.feature_importance,
                }
            return None

    def get_model_versions(self, model_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get model versions, optionally filtered by model name."""
        with self.Session() as session:
            query = select(ModelVersion)
            if model_name:
                query = query.where(ModelVersion.model_name == model_name)
            query = query.order_by(ModelVersion.trained_at.desc()).limit(limit)
            results = session.execute(query).scalars().all()

            return [
                {
                    "id": r.id,
                    "model_name": r.model_name,
                    "version": r.version,
                    "trained_at": r.trained_at.isoformat() if r.trained_at else None,
                    "is_active": r.is_active,
                    "model_path": r.model_path,
                    "train_mae": r.train_mae,
                    "train_r2": r.train_r2,
                    "test_mae": r.test_mae,
                    "test_r2": r.test_r2,
                    "overfitting": r.overfitting,
                    "n_samples": r.n_samples,
                    "best_iteration": r.best_iteration,
                }
                for r in results
            ]

    def rollback_model_version(self, model_name: str, version_id: int) -> bool:
        """Rollback to a specific model version."""
        with transaction_scope(self.Session()) as session:
            # Deactivate all versions for this model
            session.execute(
                update(ModelVersion)
                .where(ModelVersion.model_name == model_name)
                .values(is_active=0)
            )

            # Activate the specified version
            result = session.execute(
                update(ModelVersion)
                .where(ModelVersion.id == version_id, ModelVersion.model_name == model_name)
                .values(is_active=1)
            )

            return result.rowcount > 0

    # Weight Change Audit
    def create_weight_change_audit(
        self,
        old_weights: Dict[str, float],
        new_weights: Dict[str, float],
        changed_by: str,
        reason: str,
        checksum: Optional[str] = None
    ) -> int:
        """Create a weight change audit record."""
        with transaction_scope(self.Session()) as session:
            diff = {
                key: new_weights[key] - old_weights.get(key, 0)
                for key in new_weights
            }

            audit_record = WeightChangeAudit(
                changed_by=changed_by,
                reason=reason,
                old_weights=old_weights,
                new_weights=new_weights,
                diff=diff,
                checksum=checksum
            )
            session.add(audit_record)
            session.flush()
            return audit_record.id

    def get_weight_change_history(self, limit: int = 50) -> List[Dict]:
        """Get weight change history."""
        with self.Session() as session:
            results = session.execute(
                select(WeightChangeAudit)
                .order_by(WeightChangeAudit.timestamp.desc())
                .limit(limit)
            ).scalars().all()

            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "changed_by": r.changed_by,
                    "reason": r.reason,
                    "old_weights": r.old_weights,
                    "new_weights": r.new_weights,
                    "diff": r.diff,
                    "checksum": r.checksum,
                }
                for r in results
            ]
