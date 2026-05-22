"""ETL Pipeline for Real Estate Opportunity Engine."""
import asyncio
import inspect
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from loguru import logger
from pydantic import ValidationError

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, RawListing
from realestate_engine.etl.normalizer import Normalizer
from realestate_engine.etl.deduplicator import Deduplicator
from realestate_engine.etl.fuzzy_deduplicator import FuzzyDeduplicator
from realestate_engine.etl.geocoder import Geocoder
from realestate_engine.etl.enricher import Enricher
from realestate_engine.etl.validator import Validator
from realestate_engine.etl.schemas import CleanListingSchema
from realestate_engine.etl.data_quality_tracker import DataQualityTracker
from realestate_engine.etl.dead_letter_queue import DeadLetterQueue, FailureReason
from realestate_engine.monitoring.metrics import MetricsCollector
from realestate_engine.monitoring.data_quality import DataQualityEngine
from realestate_engine.utils.decorators import async_timed

metrics = MetricsCollector()
data_quality = DataQualityEngine()


def _sanitize_value(value: Any, expected_type: type = None, field_name: str = "") -> Any:
    """Sanitize a value to ensure it's not a coroutine or other invalid type for DB insertion.

    Defensive measure against 'float() argument must be a string or a real number, not coroutine'.
    DEPRECATED: Use CleanListingSchema for validation instead.
    """
    if inspect.iscoroutine(value):
        logger.error(f"Coroutine object detected in field '{field_name}' — enrichment method missing await!")
        return None
    if value is None:
        return None
    if expected_type == float:
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning(f"Cannot convert {field_name}={value!r} to float, using None")
            return None
    if expected_type == int:
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(f"Cannot convert {field_name}={value!r} to int, using None")
            return None
    if expected_type == str:
        return str(value)
    return value


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class PipelineETL:
    """ETL pipeline: Extract -> Normalize -> Deduplicate -> Geocode -> Enrich -> Validate -> Load."""
    
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.fuzzy_deduplicator = FuzzyDeduplicator()
        self.geocoder = Geocoder()
        self.enricher = Enricher()
        self.validator = Validator()
        self.quality_tracker = DataQualityTracker(metrics_collector=metrics)
    
    @async_timed
    async def run(self, batch_size: int = 500, validate_urls: bool = False, force_full: bool = False) -> int:
        """Run the full ETL pipeline on a batch of raw listings.
        
        Args:
            batch_size: Maximum number of raw listings to process
            validate_urls: Whether to validate URLs (expensive)
            force_full: If True, process all unprocessed raw listings instead of just new ones
        """

        # Purity guard: warn and skip if any fake/sample records exist
        try:
            self.repo.assert_no_sample_data()
        except RuntimeError as e:
            logger.warning(f"Sample data detected — skipping affected records: {e}")

        if force_full:
            # Process all unprocessed raw listings (backlog mode)
            raw_listings = self.repo.get_unprocessed_raw_listings(limit=batch_size)
            logger.info(f"Force full sync: processing {len(raw_listings)} unprocessed raw listings")
        else:
            # Normal mode: only process new raw listings since last ETL
            last_etl = self.repo.get_last_successful_job_execution("etl.pipeline")
            since = last_etl.finished_at if last_etl and last_etl.finished_at else None
            raw_listings = self.repo.get_raw_listings_since(since, limit=batch_size)
        if not raw_listings:
            logger.info("No new raw listings to process")
            return 0
        
        metrics.record_listings_processed("extract", len(raw_listings))
        
        # Normalize
        normalized = []
        for r in raw_listings:
            try:
                n = self.normalizer.normalize(r.raw_data, r.source_portal)
                # Casa Sapo / REMAX store source_id/source_url at record level
                if (not n.get("source_id") or n.get("source_id") == "") and r.source_id:
                    n["source_id"] = r.source_id
                    logger.debug(f"Restored source_id for {r.source_portal}: {r.source_id}")
                if (not n.get("source_url") or n.get("source_url") == "") and r.source_url:
                    n["source_url"] = r.source_url
                normalized.append(n)
            except Exception as e:
                # Add to DLQ instead of losing
                from realestate_engine.etl.dead_letter_queue import FailedRecord
                failed = FailedRecord(
                    source_portal=r.source_portal,
                    source_id=r.source_id or "",
                    raw_data=r.raw_data,
                    stage="normalization",
                    failure_reason=FailureReason.NORMALIZATION_ERROR,
                    error_message=str(e),
                    error_details=None
                )
                self.dlq.add(failed)
                logger.error(f"Normalization failed for {r.source_portal}-{r.source_id}: {e}")
                continue
        normalized = [n for n in normalized if n["preco_pedido"] and n["area_util_m2"] and n["quartos"] is not None]
        metrics.record_listings_processed("normalize", len(normalized))
        
        # Deduplicate — exact hash pass
        existing_fingerprints = self.repo.get_all_fingerprints() if hasattr(self.repo, 'get_all_fingerprints') else set()
        deduplicated = self.deduplicator.filter_duplicates(normalized, existing_fingerprints)
        metrics.record_listings_processed("deduplicate", len(deduplicated))

        # Fuzzy deduplication pass — catch near-duplicates missed by exact hash
        existing_clean = []
        try:
            if hasattr(self.repo, 'get_clean_listings_for_fuzzy'):
                existing_clean = self.repo.get_clean_listings_for_fuzzy(limit=5000)
        except Exception as _fde:
            logger.debug(f"Fuzzy dedup pool fetch skipped: {_fde}")
        deduplicated, n_fuzzy = self.fuzzy_deduplicator.filter_new_against_pool(deduplicated, existing_clean)
        if n_fuzzy:
            metrics.record_listings_processed("fuzzy_deduplicate", n_fuzzy)
        
        # Geocode
        for listing in deduplicated:
            if listing.get("morada_raw") and not listing.get("lat"):
                coords = self.geocoder.geocode(listing["morada_raw"])
                if coords:
                    listing["lat"], listing["lon"] = coords
                freg, conc = self.geocoder.extract_freguesia_concelho(listing["morada_raw"])
                if freg and not listing.get("freguesia"):
                    listing["freguesia"] = freg
                if conc and not listing.get("concelho"):
                    listing["concelho"] = conc
        metrics.record_listings_processed("geocode", len(deduplicated))
        
        # Enrich (async)
        enriched = [await self.enricher.enrich(l) for l in deduplicated]
        metrics.record_listings_processed("enrich", len(enriched))
        
        # Validate
        valid, invalid = self.validator.validate_batch(enriched, validate_url_flag=validate_urls)
        metrics.record_listings_processed("validate", len(valid))
        
        # Load
        clean_listings = []
        for data in valid:
            # Validate using Pydantic schema
            try:
                validated = CleanListingSchema(**data)
                validated_dict = validated.model_dump()
            except ValidationError as e:
                logger.error(f"Validation failed for {data.get('source_portal')}-{data.get('source_id')}: {e}")
                metrics.record_event("etl.validation_error", 1)

                # Add to DLQ
                from realestate_engine.etl.dead_letter_queue import FailedRecord
                failed = FailedRecord(
                    source_portal=data.get("source_portal", "unknown"),
                    source_id=data.get("source_id", ""),
                    raw_data=data,
                    stage="validation",
                    failure_reason=FailureReason.PYDANTIC_VALIDATION_ERROR,
                    error_message=str(e),
                    error_details=str(e)
                )
                self.dlq.add(failed)
                continue

            # Check if listing already exists to update price history
            existing = self.repo.get_clean_listing_by_source(validated_dict["source_portal"], validated_dict["source_id"])
            
            if existing:
                if existing.preco_pedido != validated_dict["preco_pedido"]:
                    logger.info(f"Price change detected for {validated_dict['source_portal']}-{validated_dict['source_id']}: {existing.preco_pedido} -> {validated_dict['preco_pedido']}")
                    from realestate_engine.database.models import PriceHistory
                    history = PriceHistory(
                        listing_id=existing.id,
                        preco=validated_dict["preco_pedido"],
                        data=datetime.now(timezone.utc).isoformat(),
                        source="spider"
                    )
                    self.repo.add_price_history(history)

                # Update existing
                self.repo.update_clean_listing(existing.id, validated_dict)
                continue

            # Create CleanListing from validated data
            clean = CleanListing(**validated_dict)
            clean_listings.append(clean)
        
        if clean_listings:
            try:
                self.repo.create_clean_listings_batch(clean_listings)
                logger.info(f"ETL pipeline completed: loaded {len(clean_listings)} clean listings")
            except Exception as e:
                logger.error(f"Database load failed: {e}")
                # Add all records to DLQ
                for data in valid:
                    try:
                        validated = CleanListingSchema(**data)
                        from realestate_engine.etl.dead_letter_queue import FailedRecord
                        failed = FailedRecord(
                            source_portal=data.get("source_portal", "unknown"),
                            source_id=data.get("source_id", ""),
                            raw_data=data,
                            stage="database",
                            failure_reason=FailureReason.DATABASE_ERROR,
                            error_message=str(e),
                            error_details=None
                        )
                        self.dlq.add(failed)
                    except Exception:
                        pass
                return 0

            # Track data quality metrics
            portal_listings = {}
            for c in clean_listings:
                portal = c.source_portal
                if portal not in portal_listings:
                    portal_listings[portal] = []
                portal_listings[portal].append(c.__dict__)

            for portal, listings in portal_listings.items():
                self.quality_tracker.track_completeness(listings, portal)
                self.quality_tracker.track_accuracy(listings, portal)
                self.quality_tracker.track_consistency(listings, portal)
                self.quality_tracker.track_uniqueness(listings, portal)

            # Alert if quality degraded
            self.quality_tracker.alert_if_degraded(threshold=85.0)

            # Get quality report
            quality_report = self.quality_tracker.get_quality_report()
            logger.info(f"Data quality report: overall_score={quality_report['overall_score']:.1f}%, total_metrics={quality_report['total_metrics']}")

            # Data quality & drift detection (FASE 7)
            try:
                dq_report = data_quality.run_full_check([c.__dict__ for c in clean_listings])
                if not dq_report["healthy"]:
                    logger.warning(f"DataQuality report: {dq_report['drift_alerts']} | anomalies={len(dq_report['price_anomalies'])} | freshness={dq_report['freshness_alerts']}")
                metrics.record_event("etl.data_quality", 1 if dq_report["healthy"] else 0)
            except Exception as e:
                logger.error(f"DataQuality check failed: {e}")
        
        return len(clean_listings)
