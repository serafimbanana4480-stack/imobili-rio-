# PHASE 3: ETL AND DATA QUALITY AUDIT
## Deduplication, Validation, Pipelines

**Date:** 2026-05-04  
**Auditor:** Principal Software Architect + Staff Engineer + Data Engineer  
**Scope:** Complete ETL pipeline analysis for production data quality  
**Production Context:** System intended for commercial sale with high-volume data processing across 8 Portuguese real estate portals

---

## EXECUTIVE SUMMARY

**Overall ETL/Data Quality Score:** 75/100

**Critical Issues:** 1  
**High Priority Issues:** 4  
**Medium Priority Issues:** 7  
**Low Priority Issues:** 3

**Key Findings:**
- ETL pipeline architecture is solid with clear stages
- Deduplication using fingerprinting is excellent and production-ready
- Normalization handles Portuguese-specific formats well
- **CRITICAL:** ETL crashes on boot due to heavy CV/NLP imports (FIXED in code but needs validation)
- **HIGH:** No schema validation using Pydantic - manual field-by-field sanitization
- **HIGH:** No data quality metrics tracking
- **HIGH:** Geocoding has no efficient caching strategy
- **HIGH:** No dead letter queue for failed records
- Enrichment is well-architected with lazy loading of heavy dependencies
- Pipeline has good error handling and logging
- No data lineage tracking
- No data versioning

---

## 1. ETL PIPELINE ARCHITECTURE ANALYSIS

### 1.1 Current Pipeline Architecture

**LOCATION:** `realestate_engine/etl/pipeline_etl.py` (223 lines)

**Architecture Pattern:**
```
Raw Listings (from Scraping)
    ↓
Normalization (Normalizer)
    ↓
Deduplication (Deduplicator - Fingerprinting)
    ↓
Geocoding (Geocoder)
    ↓
Enrichment (Enricher - INE, POIs, Amenities, CV, NLP)
    ↓
Validation (Validator)
    ↓
Loading (Repository - Clean Listings)
    ↓
Price History Update
    ↓
Data Quality Checks
```

**Code Analysis:**
```python
class PipelineETL:
    """ETL pipeline coordinating extraction, normalization, deduplication, 
    geocoding, enrichment, validation, and loading of listings."""
    
    def __init__(self):
        self.repo = DatabaseRepository()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.geocoder = Geocoder()
        self.enricher = Enricher()
        self.validator = Validator()
```

**Strengths:**
1. **Clear stage separation:** Each stage has distinct responsibility
2. **Deterministic deduplication:** Fingerprint-based dedup is excellent
3. **Lazy enrichment:** Heavy CV/NLP loaded lazily (FIX B1 from PRODUCTION_READINESS.md)
4. **Batch processing:** Supports configurable batch sizes (500-10000)
5. **Error handling:** Try/except around each stage
6. **Data quality checks:** Built-in quality validation
7. **Price history:** Automatic tracking of price changes
8. **Sample data guard:** `assert_no_sample_data()` prevents mixing test/prod data

**Production-Ready Features:**
- ✅ ACID transactions with auto-rollback
- ✅ Batch processing for scalability
- ✅ Comprehensive logging
- ✅ Metrics tracking
- ✅ Configurable batch sizes
- ✅ Force full mode for backfills

**Limitations:**
- ⚠️ No schema validation (manual sanitization)
- ⚠️ No dead letter queue for failed records
- ⚠️ No data quality metrics tracking
- ⚠️ No data lineage tracking
- ⚠️ No data versioning
- ⚠️ Serial enrichment (no parallelization)
- ⚠️ Geocoding cache is inefficient (transient only)

---

### 1.2 Normalization Analysis

**LOCATION:** `realestate_engine/etl/normalizer.py`

**Implementation Quality:** 🟢 GOOD

**Code Analysis:**
```python
class Normalizer:
    """Normalizes raw listing data from different portals into canonical format."""
    
    def normalize(self, raw_data: Dict) -> Dict:
        """Transform raw portal-specific data into canonical schema."""
        # Handles price, area, rooms, location, etc.
        # Portuguese-specific formatting (e.g., "150.000 €" → 150000)
```

**Strengths:**
1. **Portal-agnostic:** Handles data from all 8 portals
2. **Portuguese formatting:** Handles "150.000 €", "T3", etc.
3. **Type conversion:** Strings to numbers, dates, etc.
4. **Default values:** Provides sensible defaults for missing fields
5. **Location normalization:** Standardizes freguesia, concelho, distrito

**Limitations:**
- ⚠️ No schema definition (implicit schema in code)
- ⚠️ No validation rules (just conversion)
- ⚠️ No data type enforcement beyond basic conversion
- ⚠️ No enum validation (e.g., tipologia must be T1-T10)

---

## 2. CRITICAL ISSUES

### 2.1 CRITICAL ISSUE #1: ETL Boot Failure Due to Heavy Imports (PARTIALLY FIXED)

**SEVERITY:** 🔴 CRITICAL - SYSTEM UNAVAILABLE

**LOCATION:** `realestate_engine/etl/enricher.py` (lines 32-83)

**Problem (Historical - Now Fixed in Code):**
```python
# OLD CODE (BEFORE FIX):
from realestate_engine.cv.image_quality import ImageQualityAnalyzer  # Heavy
from realestate_engine.cv.image_similarity import ImageSimilarityDetector  # Heavy
from realestate_engine.nlp.bert_portuguese import BERTPortugueseProcessor  # Heavy
# These imports would fail if torch/transformers not installed
# ETL would crash on boot even if CV/NLP not used
```

**Root Cause:**
- Top-level imports of heavy ML/CV dependencies
- torch (~2GB), transformers (~500MB), ultralytics (~1GB)
- pyproject.toml has these as optional extras
- requirements.txt includes them (3GB total)
- If not installed, ETL crashes on import

**Impact on Production:**
- **System unavailable:** ETL cannot start
- **Deployment failure:** Production deploy fails if heavy deps not installed
- **Disk space:** 3GB+ dependencies for features that may not be used
- **Install time:** 10-15 minutes vs 1-2 minutes for slim install

**FIX APPLIED (Lines 38-83):**
```python
def _load_heavy_modules():
    """Best-effort lazy import of heavy CV/NLP/feature modules.
    
    Returns a dict of names mapped to either the imported callable/class or
    None when the dependency is unavailable. Logs a single info line so the
    user understands why heavy features may be skipped.
    """
    mods = {
        "extract_micro_location_features": None,
        "analyze_portuguese_description": None,
        "ImageQualityAnalyzer": None,
        "ImageSimilarityDetector": None,
        "BERTPortugueseProcessor": None,
        "SentimentAnalyzer": None,
        "NERExtractor": None,
        "DescriptionSummarizer": None,
    }
    try:
        from realestate_engine.features.micro_location import extract_micro_location_features
        mods["extract_micro_location_features"] = extract_micro_location_features
    except ImportError as e:
        logger.info(f"micro_location features disabled (missing dep): {e}")
    try:
        from realestate_engine.features.nlp_portuguese import analyze_portuguese_description
        mods["analyze_portuguese_description"] = analyze_portuguese_description
    except ImportError as e:
        logger.info(f"nlp_portuguese features disabled (missing dep): {e}")
    try:
        from realestate_engine.cv.image_quality import ImageQualityAnalyzer
        from realestate_engine.cv.image_similarity import ImageSimilarityDetector
        mods["ImageQualityAnalyzer"] = ImageQualityAnalyzer
        mods["ImageSimilarityDetector"] = ImageSimilarityDetector
    except ImportError as e:
        logger.info(f"CV enrichers disabled (install with: pip install -e .[cv]): {e}")
    try:
        from realestate_engine.nlp.bert_portuguese import BERTPortugueseProcessor
        from realestate_engine.nlp.sentiment_analyzer import SentimentAnalyzer
        from realestate_engine.nlp.ner_extractor import NERExtractor
        from realestate_engine.nlp.summarizer import DescriptionSummarizer
        mods["BERTPortugueseProcessor"] = BERTPortugueseProcessor
        mods["SentimentAnalyzer"] = SentimentAnalyzer
        mods["NERExtractor"] = NERExtractor
        mods["DescriptionSummarizer"] = DescriptionSummarizer
    except ImportError as e:
        logger.info(f"NLP enrichers disabled (install with: pip install -e .[nlp]): {e}")
    return mods
```

**Assessment:** ✅ FIX IS GOOD - Lazy loading implemented correctly

**Remaining Validation Needed:**
- [ ] Test ETL boot with slim install (no CV/NLP)
- [ ] Verify enrichment gracefully skips heavy features
- [ ] Confirm no runtime errors when heavy modules are None
- [ ] Test with full install (CV/NLP enabled)

**Validation Test Plan:**
```python
# tests/test_etl_boot_slim.py
def test_etl_boot_without_cv_nlp():
    """Test ETL boots without heavy dependencies."""
    # Install slim version
    os.system("pip install -e . --no-deps")
    os.system("pip install -r requirements-slim.txt")
    
    # Import ETL
    from realestate_engine.etl.pipeline_etl import PipelineETL
    
    # Should not raise ImportError
    pipeline = PipelineETL()
    
    # Verify heavy modules are None
    assert pipeline.enricher.image_quality_analyzer is None
    assert pipeline.enricher.bert_processor is None
    
    # Run pipeline with sample data
    result = pipeline.run(batch_size=10)
    assert result > 0  # Should succeed without CV/NLP
```

**Implementation Effort:** 1 day (validation only)  
**Priority:** CRITICAL  
**Risk:** LOW (fix already applied, just need validation)

---

## 3. HIGH PRIORITY ISSUES

### 3.1 HIGH PRIORITY ISSUE #1: No Schema Validation (Manual Sanitization)

**SEVERITY:** 🟠 HIGH - DATA QUALITY RISK

**LOCATION:** `realestate_engine/etl/pipeline_etl.py` (lines 152-206)

**Problem:**
```python
# 54 lines of repetitive manual sanitization
data["source_portal"] = _sanitize_value(data.get("source_portal", "unknown"), str, "source_portal")
data["source_id"] = _sanitize_value(data.get("source_id", ""), str, "source_id")
data["source_url"] = _sanitize_value(data.get("source_url", ""), str, "source_url")
data["scrape_timestamp"] = _sanitize_value(data.get("scrape_timestamp", ""), str, "scrape_timestamp")
data["titulo"] = _sanitize_value(data.get("titulo", ""), str, "titulo")
data["descricao"] = _sanitize_value(data.get("descricao", ""), str, "descricao")
data["preco_pedido"] = _sanitize_value(data.get("preco_pedido"), None, float, "preco_pedido")
data["area_util_m2"] = _sanitize_value(data.get("area_util_m2"), None, float, "area_util_m2")
# ... repeated 40+ times
```

**Root Cause:**
- No Pydantic schema for CleanListing
- Manual field-by-field sanitization
- No type coercion rules
- No validation rules (e.g., price > 0, area > 0)
- No enum validation (e.g., tipologia in ["T1", "T2", ...])

**Impact on Production:**
- **Maintenance:** Adding new fields requires adding sanitization code
- **Error-prone:** Easy to miss fields or make mistakes
- **Inconsistent:** Different fields may have different validation logic
- **No documentation:** Schema is implicit in code
- **Testing:** Difficult to test all validation paths
- **Type safety:** Runtime type errors instead of compile-time

**Real-World Scenario:**
```python
# Scenario: Portal sends negative price
data = {"preco_pedido": -150000}  # Invalid
# Current code:
data["preco_pedido"] = _sanitize_value(data.get("preco_pedido"), None, float)
# Result: -150000 (no validation)
# Impact: Negative price in database breaks valuation
```

**Refactor Suggestion - Pydantic Schema:**
```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TipologiaEnum(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    T6 = "T6"
    T7 = "T7"
    T8 = "T8"
    T9 = "T9"
    T10 = "T10"
    STUDIO = "Studio"

class EstadoEnum(str, Enum):
    NOVO = "Novo"
    MUITO_BOM = "Muito bom"
    BOM = "Bom"
    USADO = "Usado"
    RENOVADO = "Renovado"
    A_RENOVAR = "A renovar"

class CertificadoEnergeticoEnum(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    SEM_CERTIFICADO = "Sem certificado"

class CleanListingSchema(BaseModel):
    """Canonical schema for clean listings."""
    
    # Source fields
    source_portal: str = Field(..., min_length=1, description="Portal name")
    source_id: str = Field(..., min_length=1, description="Portal-specific ID")
    source_url: str = Field(..., min_length=1, description="Listing URL")
    scrape_timestamp: datetime = Field(..., description="Scrape timestamp")
    
    # Basic fields
    titulo: Optional[str] = Field(None, max_length=500)
    descricao: Optional[str] = Field(None, max_length=10000)
    
    # Price (must be positive)
    preco_pedido: Optional[float] = Field(None, gt=0, description="Asking price in EUR")
    preco_por_m2: Optional[float] = Field(None, gt=0)
    
    # Area (must be positive)
    area_util_m2: Optional[float] = Field(None, gt=0, description="Usable area in m²")
    area_bruta_m2: Optional[float] = Field(None, gt=0, description="Gross area in m²")
    area_terreno_m2: Optional[float] = Field(None, gt=0, description="Land area in m²")
    
    # Rooms
    quartos: Optional[int] = Field(None, ge=0, le=20, description="Number of rooms")
    casas_banho: Optional[int] = Field(None, ge=0, le=10, description="Number of bathrooms")
    
    # Typology (enum)
    tipologia: Optional[TipologiaEnum] = None
    
    # Location
    morada: Optional[str] = Field(None, max_length=500)
    freguesia: Optional[str] = Field(None, max_length=100)
    concelho: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    
    # Condition
    estado: Optional[EstadoEnum] = None
    ano_construcao: Optional[int] = Field(None, ge=1900, le=2030)
    certificado_energetico: Optional[CertificadoEnergeticoEnum] = None
    
    # Amenities (booleans)
    tem_garagem: Optional[bool] = None
    tem_piscina: Optional[bool] = None
    tem_elevador: Optional[bool] = None
    tem_terraco: Optional[bool] = None
    tem_jardim: Optional[bool] = None
    tem_ac: Optional[bool] = None
    
    # Photos
    fotos_urls: Optional[List[str]] = Field(None, max_items=50)
    
    # Sample data flag
    is_sample: int = Field(0, ge=0, le=1)
    
    @validator('preco_pedido')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @validator('area_util_m2', 'area_bruta_m2', 'area_terreno_m2')
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Area must be positive")
        return v
    
    @validator('quartos')
    def validate_rooms(cls, v):
        if v is not None and (v < 0 or v > 20):
            raise ValueError("Rooms must be between 0 and 20")
        return v
    
    @validator('fotos_urls')
    def validate_photos(cls, v):
        if v is not None:
            valid_urls = [url for url in v if url.startswith(('http://', 'https://'))]
            if len(valid_urls) != len(v):
                raise ValueError("All photo URLs must be valid HTTP/HTTPS URLs")
        return v
    
    class Config:
        extra = "forbid"  # Reject unknown fields
        validate_assignment = True  # Validate on assignment

# Usage in ETL
class PipelineETL:
    def normalize_and_validate(self, raw_data: Dict) -> Dict:
        """Normalize and validate raw data."""
        normalized = self.normalizer.normalize(raw_data)
        
        try:
            validated = CleanListingSchema(**normalized)
            return validated.dict()
        except ValidationError as e:
            logger.error(f"Validation failed for listing {raw_data.get('source_id')}: {e}")
            # Handle validation error
            # Option 1: Skip record
            # Option 2: Use defaults
            # Option 3: Send to dead letter queue
            raise DataValidationError(str(e))
```

**Benefits:**
- **Type safety:** Compile-time type checking
- **Validation:** Automatic validation rules
- **Documentation:** Schema is self-documenting
- **Error messages:** Clear, actionable error messages
- **Enum validation:** Ensures valid values
- **Field constraints:** Min/max, regex patterns
- **Unknown fields:** Rejects unexpected fields
- **Testing:** Easy to test validation logic

**Migration Strategy:**
```python
# Phase 1: Add Pydantic schema alongside existing code
# Phase 2: Run both in parallel, log differences
# Phase 3: Switch to Pydantic-only
# Phase 4: Remove old sanitization code
```

**Implementation Effort:** 3-4 days  
**Priority:** HIGH  
**Risk:** MEDIUM (core ETL logic)

---

### 3.2 HIGH PRIORITY ISSUE #2: No Data Quality Metrics Tracking

**SEVERITY:** 🟠 HIGH - NO VISIBILITY

**LOCATION:** Missing component

**Problem:**
- No tracking of data quality metrics
- No monitoring of completeness (missing fields)
- No monitoring of accuracy (invalid values)
- No monitoring of consistency (cross-field validation)
- No alerting for data quality degradation

**Impact on Production:**
- **No visibility:** Cannot tell if data quality is degrading
- **Silent failures:** Bad data enters system without notification
- **No debugging:** Difficult to identify data quality issues
- **No optimization:** Cannot identify problematic portals

**Refactor Suggestion:**
```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class DataQualityDimension(Enum):
    COMPLETENESS = "completeness"  # % of non-null fields
    ACCURACY = "accuracy"  # % of valid values
    CONSISTENCY = "consistency"  # % of consistent cross-field values
    TIMELINESS = "timeliness"  # age of data
    UNIQUENESS = "uniqueness"  # % of unique records

@dataclass
class DataQualityMetric:
    dimension: DataQualityDimension
    field: str
    total_count: int
    valid_count: int
    invalid_count: int
    score: float  # 0-100
    timestamp: datetime
    portal: str

class DataQualityTracker:
    """Track data quality metrics across ETL pipeline."""
    
    def __init__(self):
        self.metrics: List[DataQualityMetric] = []
    
    def track_completeness(self, listings: List[Dict], portal: str):
        """Track field completeness."""
        required_fields = [
            "source_portal", "source_id", "preco_pedido", "area_util_m2",
            "quartos", "freguesia", "concelho", "distrito"
        ]
        
        for field in required_fields:
            total = len(listings)
            valid = sum(1 for listing in listings if listing.get(field) is not None)
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0
            
            metric = DataQualityMetric(
                dimension=DataQualityDimension.COMPLETENESS,
                field=field,
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)
            
            if score < 80:
                logger.warning(
                    f"Low completeness for {field} in {portal}: {score:.1f}% "
                    f"({valid}/{total})"
                )
    
    def track_accuracy(self, listings: List[Dict], portal: str):
        """Track field accuracy (valid values)."""
        accuracy_checks = {
            "preco_pedido": lambda x: x is not None and x > 0,
            "area_util_m2": lambda x: x is not None and x > 0,
            "quartos": lambda x: x is not None and 0 <= x <= 20,
            "lat": lambda x: x is not None and -90 <= x <= 90,
            "lon": lambda x: x is not None and -180 <= x <= 180,
        }
        
        for field, check in accuracy_checks.items():
            total = len(listings)
            valid = sum(1 for listing in listings if check(listing.get(field)))
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0
            
            metric = DataQualityMetric(
                dimension=DataQualityDimension.ACCURACY,
                field=field,
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)
            
            if score < 90:
                logger.warning(
                    f"Low accuracy for {field} in {portal}: {score:.1f}% "
                    f"({valid}/{total})"
                )
    
    def track_consistency(self, listings: List[Dict], portal: str):
        """Track cross-field consistency."""
        consistency_checks = [
            # Price per m² should be reasonable (100-10000 EUR/m²)
            lambda x: x.get("preco_por_m2") is None or 100 <= x.get("preco_por_m2") <= 10000,
            # Area should match rooms (T1: 30-80m², T3: 60-150m², etc.)
            # This is simplified - real logic more complex
        ]
        
        for check in consistency_checks:
            total = len(listings)
            valid = sum(1 for listing in listings if check(listing))
            invalid = total - valid
            score = (valid / total * 100) if total > 0 else 0
            
            metric = DataQualityMetric(
                dimension=DataQualityDimension.CONSISTENCY,
                field="cross_field",
                total_count=total,
                valid_count=valid,
                invalid_count=invalid,
                score=score,
                timestamp=datetime.now(),
                portal=portal
            )
            self.metrics.append(metric)
    
    def get_quality_report(self, portal: str = None) -> Dict:
        """Generate quality report."""
        metrics = self.metrics if portal is None else [m for m in self.metrics if m.portal == portal]
        
        report = {
            "overall_score": sum(m.score for m in metrics) / len(metrics) if metrics else 0,
            "by_dimension": {},
            "by_field": {},
            "by_portal": {}
        }
        
        # Group by dimension
        for dim in DataQualityDimension:
            dim_metrics = [m for m in metrics if m.dimension == dim]
            if dim_metrics:
                report["by_dimension"][dim.value] = {
                    "score": sum(m.score for m in dim_metrics) / len(dim_metrics),
                    "metrics": dim_metrics
                }
        
        # Group by field
        for metric in metrics:
            if metric.field not in report["by_field"]:
                report["by_field"][metric.field] = []
            report["by_field"][metric.field].append(metric)
        
        # Group by portal
        for metric in metrics:
            if metric.portal not in report["by_portal"]:
                report["by_portal"][metric.portal] = []
            report["by_portal"][metric.portal].append(metric)
        
        return report
    
    def alert_if_degraded(self, threshold: float = 80.0):
        """Alert if quality score below threshold."""
        report = self.get_quality_report()
        
        if report["overall_score"] < threshold:
            logger.error(
                f"Data quality degraded: {report['overall_score']:.1f}% "
                f"(threshold: {threshold}%)"
            )
            # Send alert
            # self.alert_manager.send_alert(...)
        
        # Check individual dimensions
        for dim_name, dim_data in report["by_dimension"].items():
            if dim_data["score"] < threshold:
                logger.error(
                    f"Data quality degraded for {dim_name}: {dim_data['score']:.1f}% "
                    f"(threshold: {threshold}%)"
                )

# Integration with ETL
class PipelineETL:
    def __init__(self):
        self.quality_tracker = DataQualityTracker()
    
    async def run(self, batch_size: int = 500):
        # ... existing ETL logic ...
        
        # Track data quality
        self.quality_tracker.track_completeness(clean_listings, portal="imovirtual")
        self.quality_tracker.track_accuracy(clean_listings, portal="imovirtual")
        self.quality_tracker.track_consistency(clean_listings, portal="imovirtual")
        
        # Alert if degraded
        self.quality_tracker.alert_if_degraded(threshold=85.0)
        
        # Get quality report
        report = self.quality_tracker.get_quality_report()
        logger.info(f"Data quality report: {report}")
```

**Integration with Prometheus:**
```python
# Add to MetricsCollector
class MetricsCollector:
    def __init__(self):
        # ... existing metrics ...
        
        # Data quality metrics
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Data quality score by dimension and field',
            ['dimension', 'field', 'portal']
        )
        self.data_quality_completeness = Gauge(
            'data_quality_completeness',
            'Field completeness percentage',
            ['field', 'portal']
        )
        self.data_quality_accuracy = Gauge(
            'data_quality_accuracy',
            'Field accuracy percentage',
            ['field', 'portal']
        )

# Update DataQualityTracker
class DataQualityTracker:
    def __init__(self):
        self.metrics = MetricsCollector()
    
    def track_completeness(self, listings: List[Dict], portal: str):
        # ... existing logic ...
        
        # Update Prometheus
        self.metrics.data_quality_completeness.labels(field=field, portal=portal).set(score)
```

**Implementation Effort:** 3 days  
**Priority:** HIGH  
**Risk:** LOW

---

### 3.3 HIGH PRIORITY ISSUE #3: No Dead Letter Queue for Failed Records

**SEVERITY:** 🟠 HIGH - DATA LOSS RISK

**LOCATION:** `realestate_engine/etl/pipeline_etl.py`

**Problem:**
```python
# Current error handling
try:
    normalized = self.normalizer.normalize(raw_data)
except Exception as e:
    logger.error(f"Normalization failed for {raw_data.get('source_id')}: {e}")
    continue  # Skip record - DATA LOSS
```

**Root Cause:**
- Failed records are logged but not persisted
- No retry mechanism for failed records
- No investigation of why records failed
- No recovery mechanism

**Impact on Production:**
- **Data loss:** Failed records are lost forever
- **No visibility:** Cannot tell which records failed
- **No recovery:** Cannot reprocess failed records
- **No investigation:** Cannot debug why records failed

**Real-World Scenario:**
```
Day 1: 1000 listings scraped, 50 fail normalization
Day 2: 50 listings lost, never recovered
Day 3: Bug in normalizer fixed
Day 4: Cannot recover lost 50 listings from Day 1
```

**Refactor Suggestion:**
```python
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

class FailureReason(Enum):
    NORMALIZATION_ERROR = "normalization_error"
    DEDUPLICATION_ERROR = "deduplication_error"
    GEOCODING_ERROR = "geocoding_error"
    ENRICHMENT_ERROR = "enrichment_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"

@dataclass
class FailedRecord:
    """Record that failed during ETL processing."""
    source_portal: str
    source_id: str
    raw_data: Dict[str, Any]
    stage: str  # normalization, deduplication, geocoding, etc.
    failure_reason: FailureReason
    error_message: str
    error_details: Optional[str] = None
    timestamp: datetime = None
    retry_count: int = 0
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DeadLetterQueue:
    """Dead letter queue for failed ETL records."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
    
    def add(self, failed_record: FailedRecord):
        """Add failed record to DLQ."""
        logger.warning(
            f"Adding to DLQ: {failed_record.source_portal}/{failed_record.source_id} "
            f"at stage {failed_record.stage}: {failed_record.error_message}"
        )
        # Store in database (new table: failed_records)
        self.repo.create_failed_record(failed_record)
    
    def get_unresolved(self, limit: int = 100) -> List[FailedRecord]:
        """Get unresolved failed records."""
        return self.repo.get_failed_records(resolved=False, limit=limit)
    
    def mark_resolved(self, record_id: int):
        """Mark failed record as resolved."""
        self.repo.update_failed_record(record_id, resolved=True)
    
    def retry_record(self, failed_record: FailedRecord, pipeline: PipelineETL) -> bool:
        """Retry processing a failed record."""
        failed_record.retry_count += 1
        
        try:
            # Retry from the failed stage
            if failed_record.stage == "normalization":
                normalized = pipeline.normalizer.normalize(failed_record.raw_data)
                # Continue with rest of pipeline
                # ...
            elif failed_record.stage == "geocoding":
                # Retry geocoding
                # ...
            
            # If successful, mark as resolved
            self.mark_resolved(failed_record.id)
            logger.info(f"Successfully retried {failed_record.source_id}")
            return True
        except Exception as e:
            logger.error(f"Retry failed for {failed_record.source_id}: {e}")
            # Update error message
            self.repo.update_failed_record(
                failed_record.id,
                error_message=str(e),
                retry_count=failed_record.retry_count
            )
            return False
    
    def get_stats(self) -> Dict:
        """Get DLQ statistics."""
        total = self.repo.count_failed_records()
        unresolved = self.repo.count_failed_records(resolved=False)
        by_reason = self.repo.count_failed_records_by_reason()
        by_stage = self.repo.count_failed_records_by_stage()
        
        return {
            "total_failed": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_reason": by_reason,
            "by_stage": by_stage
        }

# Integration with ETL
class PipelineETL:
    def __init__(self):
        self.dlq = DeadLetterQueue(self.repo)
    
    async def run(self, batch_size: int = 500):
        raw_listings = self.repo.get_raw_listings(limit=batch_size)
        
        for raw in raw_listings:
            try:
                normalized = self.normalizer.normalize(raw.raw_data)
            except Exception as e:
                # Add to DLQ instead of losing
                failed = FailedRecord(
                    source_portal=raw.source_portal,
                    source_id=raw.source_id,
                    raw_data=raw.raw_data,
                    stage="normalization",
                    failure_reason=FailureReason.NORMALIZATION_ERROR,
                    error_message=str(e),
                    error_details=traceback.format_exc()
                )
                self.dlq.add(failed)
                continue
            
            # ... continue with pipeline ...

# Add database table for failed_records
# models.py
class FailedRecord(Base):
    __tablename__ = "failed_records"
    
    id = Column(Integer, primary_key=True)
    source_portal = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    raw_data = Column(JSON, nullable=False)
    stage = Column(String(50), nullable=False)
    failure_reason = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(UTC))
    retry_count = Column(Integer, default=0)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_failed_records_portal_stage', 'source_portal', 'stage'),
        Index('idx_failed_records_resolved', 'resolved'),
    )
```

**Benefits:**
- **No data loss:** Failed records are persisted
- **Visibility:** Can see which records failed and why
- **Recovery:** Can retry failed records after fixes
- **Investigation:** Can debug issues using failed records
- **Metrics:** Can track failure rates by stage/portal

**Implementation Effort:** 3 days  
**Priority:** HIGH  
**Risk:** MEDIUM (requires database migration)

---

### 3.4 HIGH PRIORITY ISSUE #4: Inefficient Geocoding Cache

**SEVERITY:** 🟠 HIGH - PERFORMANCE RISK

**LOCATION:** `realestate_engine/etl/enricher.py` (lines 130-166)

**Problem:**
```python
@lru_cache(maxsize=512)
def _poi_cache_key(self, lat_rounded: str, lon_rounded: str, category: str) -> float:
    """Cached POI distance lookup with rounded coordinates (~100m precision)."""
    return -1.0  # placeholder; real logic in enrich_pois

async def enrich_pois(self, listing: Dict) -> Dict:
    """Add Points of Interest distances (async) with coordinate-based caching."""
    lat, lon = listing.get("lat"), listing.get("lon")
    if lat and lon:
        lat_r = round(float(lat), 3)
        lon_r = round(float(lon), 3)
        
        # Check instance-level transient cache (resets per batch)
        if not hasattr(self, "_poi_transient_cache"):
            self._poi_transient_cache: Dict[tuple, Dict[str, Optional[float]]] = {}
        
        if cache_key not in self._poi_transient_cache:
            self._poi_transient_cache[cache_key] = {
                "metro": await self.poi_client.get_nearest_distance(lat_r, lon_r, "metro"),
                "school": await self.poi_client.get_nearest_distance(lat_r, lon_r, "school"),
                "market": await self.poi_client.get_nearest_distance(lat_r, lon_r, "market"),
            }
```

**Root Cause:**
- Cache is transient (resets per batch)
- No distributed cache (Redis)
- No cache persistence across ETL runs
- No cache expiration
- No cache size limit (unbounded growth)

**Impact on Production:**
- **Repeated API calls:** Same coordinates geocoded multiple times
- **Performance:** Slow ETL due to repeated geocoding
- **API costs:** Wasted API calls to geocoding service
- **Rate limits:** May hit geocoding API rate limits

**Real-World Scenario:**
```
Run 1: Geocode 1000 listings (1000 API calls)
Run 2: Geocode 900 new listings + 100 duplicates (1000 API calls)
Run 3: Geocode 800 new listings + 200 duplicates (1000 API calls)
Total: 3000 API calls for 1000 unique locations
With Redis cache: 1000 API calls (67% reduction)
```

**Refactor Suggestion:**
```python
import redis.asyncio as aioredis
import json
from typing import Optional, Dict
import hashlib

class DistributedGeocodingCache:
    """Distributed geocoding cache using Redis."""
    
    def __init__(self, redis_url: str, ttl: int = 86400):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl: Cache TTL in seconds (default: 24 hours)
        """
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl
    
    def _cache_key(self, lat: float, lon: float, category: str) -> str:
        """Generate cache key."""
        # Round to 3 decimal places (~100m precision)
        lat_r = round(lat, 3)
        lon_r = round(lon, 3)
        key = f"geocode:{category}:{lat_r}:{lon_r}"
        return key
    
    async def get(self, lat: float, lon: float, category: str) -> Optional[float]:
        """Get cached geocoding result."""
        key = self._cache_key(lat, lon, category)
        cached = await self.redis.get(key)
        
        if cached:
            logger.debug(f"Cache HIT: {key}")
            return float(cached)
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(self, lat: float, lon: float, category: str, value: float):
        """Cache geocoding result."""
        key = self._cache_key(lat, lon, category)
        await self.redis.setex(key, self.ttl, str(value))
        logger.debug(f"Cache SET: {key} = {value}")
    
    async def get_batch(self, coords: List[tuple], category: str) -> Dict[tuple, Optional[float]]:
        """Get multiple cached results at once."""
        keys = [self._cache_key(lat, lon, category) for lat, lon in coords]
        cached_values = await self.redis.mget(keys)
        
        result = {}
        for (lat, lon), value in zip(coords, cached_values):
            if value:
                result[(lat, lon)] = float(value)
            else:
                result[(lat, lon)] = None
        
        return result
    
    async def set_batch(self, results: Dict[tuple, float], category: str):
        """Set multiple cached results at once."""
        pipe = self.redis.pipeline()
        
        for (lat, lon), value in results.items():
            key = self._cache_key(lat, lon, category)
            pipe.setex(key, self.ttl, str(value))
        
        await pipe.execute()
    
    async def invalidate(self, lat: float, lon: float, category: str):
        """Invalidate cache entry."""
        key = self._cache_key(lat, lon, category)
        await self.redis.delete(key)
    
    async def get_stats(self) -> Dict:
        """Get cache statistics."""
        info = await self.redis.info("stats")
        return {
            "total_keys": info.get("keyspace", 0),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }

# Integration with Enricher
class Enricher:
    def __init__(self):
        self.repo = DatabaseRepository()
        self.poi_client = POIClient()
        self.ine_client = INEClient()
        
        # Use distributed cache if Redis is configured
        if config.redis_url:
            self.geo_cache = DistributedGeocodingCache(config.redis_url, ttl=86400)
        else:
            # Fallback to transient cache
            self._poi_transient_cache: Dict[tuple, Dict[str, Optional[float]]] = {}
    
    async def enrich_pois(self, listing: Dict) -> Dict:
        """Add Points of Interest distances with distributed caching."""
        lat, lon = listing.get("lat"), listing.get("lon")
        
        if not lat or not lon:
            return listing
        
        categories = ["metro", "school", "market"]
        results = {}
        
        if hasattr(self, 'geo_cache'):
            # Use distributed cache
            for category in categories:
                cached = await self.geo_cache.get(lat, lon, category)
                if cached is not None:
                    results[f"dist_{category}_m"] = cached
                else:
                    # Cache miss - fetch from API
                    distance = await self.poi_client.get_nearest_distance(lat, lon, category)
                    results[f"dist_{category}_m"] = distance
                    await self.geo_cache.set(lat, lon, category, distance)
        else:
            # Fallback to transient cache
            lat_r = round(float(lat), 3)
            lon_r = round(float(lon), 3)
            cache_key = (lat_r, lon_r)
            
            if not hasattr(self, "_poi_transient_cache"):
                self._poi_transient_cache = {}
            
            if cache_key not in self._poi_transient_cache:
                self._poi_transient_cache[cache_key] = {
                    "metro": await self.poi_client.get_nearest_distance(lat_r, lon_r, "metro"),
                    "school": await self.poi_client.get_nearest_distance(lat_r, lon_r, "school"),
                    "market": await self.poi_client.get_nearest_distance(lat_r, lon_r, "market"),
                }
            
            results = self._poi_transient_cache[cache_key]
        
        listing.update(results)
        return listing
```

**Benefits:**
- **Performance:** 10-100x faster for cached coordinates
- **Cost reduction:** 90%+ reduction in API calls
- **Scalability:** Distributed cache works across multiple workers
- **Persistence:** Cache survives ETL restarts
- **Metrics:** Track cache hit rate

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** MEDIUM (requires Redis)

---

## 4. MEDIUM PRIORITY ISSUES

### 4.1 MEDIUM PRIORITY ISSUE #1: No Data Lineage Tracking

**SEVERITY:** 🟡 MEDIUM - DEBUGGING DIFFICULTY

**LOCATION:** Missing component

**Problem:**
- No tracking of data transformations
- No audit trail of how data changed
- No ability to trace data from source to destination
- Difficult to debug data quality issues

**Refactor Suggestion:**
```python
@dataclass
class DataLineageEvent:
    """Record of data transformation."""
    record_id: str
    stage: str
    input_data: Dict
    output_data: Dict
    transformation_type: str
    timestamp: datetime
    portal: str

class DataLineageTracker:
    """Track data lineage through ETL pipeline."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
    
    def record_transformation(
        self,
        record_id: str,
        stage: str,
        input_data: Dict,
        output_data: Dict,
        transformation_type: str,
        portal: str
    ):
        """Record a data transformation."""
        event = DataLineageEvent(
            record_id=record_id,
            stage=stage,
            input_data=input_data,
            output_data=output_data,
            transformation_type=transformation_type,
            timestamp=datetime.now(),
            portal=portal
        )
        self.repo.create_lineage_event(event)
    
    def get_lineage(self, record_id: str) -> List[DataLineageEvent]:
        """Get lineage for a specific record."""
        return self.repo.get_lineage_events(record_id)
```

**Implementation Effort:** 2 days  
**Priority:** MEDIUM  
**Risk:** LOW

---

### 4.2 MEDIUM PRIORITY ISSUE #2: No Data Versioning

**SEVERITY:** 🟡 MEDIUM - NO ROLLBACK

**LOCATION:** Missing component

**Problem:**
- No versioning of data schemas
- No ability to rollback data changes
- Difficult to manage schema migrations
- No data schema history

**Refactor Suggestion:**
```python
class DataVersionManager:
    """Manage data schema versions."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
        self.current_version = self._get_current_version()
    
    def _get_current_version(self) -> int:
        """Get current data schema version."""
        version = self.repo.get_config("data_schema_version")
        return int(version) if version else 1
    
    def migrate(self, target_version: int):
        """Migrate data to target version."""
        for version in range(self.current_version, target_version + 1):
            self._apply_migration(version)
        
        self.repo.set_config("data_schema_version", str(target_version))
        self.current_version = target_version
    
    def _apply_migration(self, version: int):
        """Apply migration for specific version."""
        # Migration logic
        pass
```

**Implementation Effort:** 3 days  
**Priority:** MEDIUM  
**Risk:** MEDIUM

---

### 4.3 Additional Medium Priority Issues

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 3 | No parallel enrichment | enricher.py | MEDIUM | 2 days | MEDIUM |
| 4 | No data profiling | Missing | LOW | 2 days | MEDIUM |
| 5 | No anomaly detection | Missing | MEDIUM | 3 days | MEDIUM |
| 6 | No data governance policies | Missing | MEDIUM | 5 days | MEDIUM |
| 7 | No data catalog | Missing | LOW | 3 days | MEDIUM |

---

## 5. LOW PRIORITY ISSUES

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 1 | No data sampling for testing | pipeline_etl.py | LOW | 1 day | LOW |
| 2 | No data retention policy | Missing | LOW | 1 day | LOW |
| 3 | No data archival strategy | Missing | LOW | 2 days | LOW |

---

## 6. REFACTOR ROADMAP

### Phase 1: Critical Fixes (Week 1)
- [ ] Validate ETL boot with slim install (no CV/NLP)
- [ ] Test enrichment gracefully skips heavy features
- [ ] Confirm no runtime errors when heavy modules are None

### Phase 2: High Priority (Week 2-3)
- [ ] Implement Pydantic schema for CleanListing
- [ ] Add data quality metrics tracking
- [ ] Implement dead letter queue for failed records
- [ ] Implement distributed geocoding cache (Redis)

### Phase 3: Medium Priority (Week 4-5)
- [ ] Implement data lineage tracking
- [ ] Implement data versioning
- [ ] Add parallel enrichment
- [ ] Implement data profiling

### Phase 4: Low Priority (Week 6)
- [ ] Add data sampling for testing
- [ ] Define data retention policy
- [ ] Implement data archival strategy

---

## 7. PRODUCTION READINESS SCORE

**ETL/Data Quality Audit Score: 75/100**

**Breakdown:**
- Pipeline Architecture: 85/100 (excellent stage separation)
- Normalization: 80/100 (good Portuguese formatting)
- Deduplication: 95/100 (excellent fingerprinting)
- Validation: 40/100 (no schema validation)
- Data Quality Tracking: 30/100 (no metrics)
- Error Handling: 70/100 (good but no DLQ)
- Caching: 50/100 (transient only)
- Performance: 75/100 (serial enrichment)

**Recommendation:** Implement Pydantic schema validation and data quality metrics before production deployment. These are foundational for data quality assurance.

---

**End of Phase 3: ETL and Data Quality Audit**
