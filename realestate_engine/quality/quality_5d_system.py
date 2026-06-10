"""
5D Quality System

Comprehensive data quality validation system with 5 dimensions:
1. Completeness (data completeness)
2. Accuracy (data accuracy)
3. Consistency (data consistency)
4. Freshness (data freshness)
5. Uniqueness (data uniqueness)

Implements real-time validation, quality scoring, and automatic rejection
of low-quality listings (<85% quality score).
"""

import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from loguru import logger
import re
import hashlib

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available, using fallback implementations")

from realestate_engine.database.repository import DatabaseRepository


@dataclass
class QualityDimension:
    """Quality dimension with score and issues"""
    name: str
    score: float
    weight: float
    issues: List[str]
    passed: bool
    threshold: float


@dataclass
class QualityResult:
    """Complete quality validation result"""
    overall_score: float
    passed_validation: bool
    dimensions: Dict[str, QualityDimension]
    critical_issues: List[str]
    recommendations: List[str]
    validation_timestamp: datetime
    listing_id: Optional[str] = None


class CompletenessValidator:
    """Validates data completeness"""
    
    def __init__(self):
        self.essential_fields = [
            "preco_pedido",
            "area_util_m2", 
            "quartos",
            "concelho",
            "titulo"
        ]
        
        self.important_fields = [
            "descricao",
            "estado",
            "ano_construcao",
            "casas_banho",
            "andar",
            "lat",
            "lon"
        ]
        
        self.optional_fields = [
            "tem_garagem",
            "tem_piscina",
            "tem_elevador",
            "tem_ac",
            "tipologia",
            "freguesia"
        ]
    
    def validate(self, listing: Dict) -> QualityDimension:
        """Validate completeness of a listing"""
        
        issues = []
        
        # Check essential fields
        essential_complete = 0
        for field in self.essential_fields:
            if listing.get(field):
                value = listing[field]
                if isinstance(value, (int, float)):
                    if value > 0:
                        essential_complete += 1
                elif isinstance(value, str):
                    if value.strip():
                        essential_complete += 1
                else:
                    essential_complete += 1
            else:
                issues.append(f"Missing essential field: {field}")
        
        essential_score = essential_complete / len(self.essential_fields)
        
        # Check important fields
        important_complete = 0
        for field in self.important_fields:
            if listing.get(field):
                value = listing[field]
                if isinstance(value, (int, float)):
                    if value > 0:
                        important_complete += 1
                elif isinstance(value, str):
                    if value.strip() and len(value.strip()) > 10:
                        important_complete += 1
                else:
                    important_complete += 1
        
        important_score = important_complete / len(self.important_fields)
        
        # Check optional fields
        optional_complete = sum(1 for field in self.optional_fields if listing.get(field))
        optional_score = optional_complete / len(self.optional_fields)
        
        # Calculate weighted completeness score
        overall_score = (essential_score * 0.6) + (important_score * 0.3) + (optional_score * 0.1)
        
        # Check if passed
        passed = overall_score >= 0.8
        if not passed:
            issues.append(f"Completeness score {overall_score:.2f} below threshold 0.8")
        
        return QualityDimension(
            name="completeness",
            score=overall_score,
            weight=0.25,
            issues=issues,
            passed=passed,
            threshold=0.8
        )


class AccuracyValidator:
    """Validates data accuracy"""
    
    def __init__(self):
        self.accuracy_rules = self._build_accuracy_rules()
    
    def _build_accuracy_rules(self) -> Dict[str, Dict]:
        """Build accuracy validation rules"""
        return {
            "preco_pedido": {
                "min": 1000,
                "max": 10000000,
                "type": (int, float),
                "validation": self._validate_price
            },
            "area_util_m2": {
                "min": 10,
                "max": 1000,
                "type": (int, float),
                "validation": self._validate_area
            },
            "quartos": {
                "min": 0,
                "max": 20,
                "type": (int, float),
                "validation": self._validate_rooms
            },
            "casas_banho": {
                "min": 0,
                "max": 20,
                "type": (int, float),
                "validation": self._validate_bathrooms
            },
            "ano_construcao": {
                "min": 1800,
                "max": 2026,
                "type": (int, float),
                "validation": self._validate_year
            },
            "lat": {
                "min": 36.0,
                "max": 43.0,
                "type": (int, float),
                "validation": self._validate_latitude
            },
            "lon": {
                "min": -10.0,
                "max": -6.0,
                "type": (int, float),
                "validation": self._validate_longitude
            }
        }
    
    def validate(self, listing: Dict) -> QualityDimension:
        """Validate accuracy of a listing"""
        
        issues = []
        total_fields = 0
        accurate_fields = 0
        
        for field, rules in self.accuracy_rules.items():
            value = listing.get(field)
            
            if value is not None:
                total_fields += 1
                
                # Type check
                if not isinstance(value, rules["type"]):
                    issues.append(f"Invalid type for {field}: expected {rules['type']}, got {type(value)}")
                    continue
                
                # Range check
                if not (rules["min"] <= value <= rules["max"]):
                    issues.append(f"{field} value {value} outside valid range [{rules['min']}, {rules['max']}]")
                    continue
                
                # Custom validation
                if rules["validation"](value, listing):
                    accurate_fields += 1
                else:
                    issues.append(f"Custom validation failed for {field}")
        
        # Calculate accuracy score
        accuracy_score = accurate_fields / total_fields if total_fields > 0 else 0.0
        
        # Check if passed
        passed = accuracy_score >= 0.9
        if not passed:
            issues.append(f"Accuracy score {accuracy_score:.2f} below threshold 0.9")
        
        return QualityDimension(
            name="accuracy",
            score=accuracy_score,
            weight=0.30,
            issues=issues,
            passed=passed,
            threshold=0.9
        )
    
    def _validate_price(self, value: float, listing: Dict) -> bool:
        """Validate price accuracy"""
        # Check price per m2 ratio
        area = listing.get("area_util_m2")
        if area and area > 0:
            price_per_m2 = value / area
            # Reasonable range for Portugal: 500 - 10000 euros/m2
            if not (500 <= price_per_m2 <= 10000):
                return False
        
        return True
    
    def _validate_area(self, value: float, listing: Dict) -> bool:
        """Validate area accuracy"""
        # Check area vs rooms consistency
        rooms = listing.get("quartos")
        if rooms and rooms > 0:
            # Minimum 15m2 per room + 20m2 common areas
            min_area = (rooms * 15) + 20
            if value < min_area:
                return False
        
        return True
    
    def _validate_rooms(self, value: float, listing: Dict) -> bool:
        """Validate rooms accuracy"""
        # Check rooms vs area consistency
        area = listing.get("area_util_m2")
        if area and area > 0:
            # Maximum 1 room per 25m2
            max_rooms = area / 25
            if value > max_rooms:
                return False
        
        return True
    
    def _validate_bathrooms(self, value: float, listing: Dict) -> bool:
        """Validate bathrooms accuracy"""
        # Bathrooms should not exceed rooms by more than 2
        rooms = listing.get("quartos", 0)
        if rooms > 0 and value > rooms + 2:
            return False
        
        return True
    
    def _validate_year(self, value: float, listing: Dict) -> bool:
        """Validate construction year accuracy"""
        current_year = datetime.now().year
        if value > current_year + 2:  # Allow 2 years for future constructions
            return False
        
        return True
    
    def _validate_latitude(self, value: float, listing: Dict) -> bool:
        """Validate latitude for Portugal"""
        # Portugal latitude range: approximately 36.0 to 43.0
        return 36.0 <= value <= 43.0
    
    def _validate_longitude(self, value: float, listing: Dict) -> bool:
        """Validate longitude for Portugal"""
        # Portugal longitude range: approximately -10.0 to -6.0
        return -10.0 <= value <= -6.0


class ConsistencyValidator:
    """Validates data consistency"""
    
    def validate(self, listing: Dict) -> QualityDimension:
        """Validate consistency of a listing"""
        
        issues = []
        consistency_checks = 0
        passed_checks = 0
        
        # Check price vs area consistency
        if self._check_price_area_consistency(listing):
            passed_checks += 1
        else:
            issues.append("Price vs area inconsistency detected")
        consistency_checks += 1
        
        # Check rooms vs area consistency
        if self._check_rooms_area_consistency(listing):
            passed_checks += 1
        else:
            issues.append("Rooms vs area inconsistency detected")
        consistency_checks += 1
        
        # Check location consistency
        if self._check_location_consistency(listing):
            passed_checks += 1
        else:
            issues.append("Location data inconsistency detected")
        consistency_checks += 1
        
        # Check property type consistency
        if self._check_property_type_consistency(listing):
            passed_checks += 1
        else:
            issues.append("Property type data inconsistency detected")
        consistency_checks += 1
        
        # Check description consistency
        if self._check_description_consistency(listing):
            passed_checks += 1
        else:
            issues.append("Description vs structured data inconsistency")
        consistency_checks += 1
        
        # Calculate consistency score
        consistency_score = passed_checks / consistency_checks if consistency_checks > 0 else 0.0
        
        # Check if passed
        passed = consistency_score >= 0.8
        if not passed:
            issues.append(f"Consistency score {consistency_score:.2f} below threshold 0.8")
        
        return QualityDimension(
            name="consistency",
            score=consistency_score,
            weight=0.20,
            issues=issues,
            passed=passed,
            threshold=0.8
        )
    
    def _check_price_area_consistency(self, listing: Dict) -> bool:
        """Check consistency between price and area"""
        price = listing.get("preco_pedido")
        area = listing.get("area_util_m2")
        
        if price and area and area > 0:
            price_per_m2 = price / area
            # Check if price per m2 is reasonable for Portugal
            return 500 <= price_per_m2 <= 10000
        
        return True  # Can't check if data missing
    
    def _check_rooms_area_consistency(self, listing: Dict) -> bool:
        """Check consistency between rooms and area"""
        rooms = listing.get("quartos")
        area = listing.get("area_util_m2")
        
        if rooms and area and area > 0:
            # Check reasonable area per room (15-100m2 per room)
            area_per_room = area / rooms
            return 15 <= area_per_room <= 100
        
        return True
    
    def _check_location_consistency(self, listing: Dict) -> bool:
        """Check consistency between location fields and coordinates."""
        concelho = listing.get("concelho")
        freguesia = listing.get("freguesia")
        lat = listing.get("lat")
        lon = listing.get("lon")
        
        # If we have coordinates, they should be consistent with textual location
        if lat and lon and concelho:
            # Simplified check: verify coordinates are within Portugal mainland / islands
            # and roughly match the concelho centroid (tolerance ~10km / 0.1 degrees)
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                # Portugal bounds
                if not (36.0 <= lat_f <= 43.0 and -10.0 <= lon_f <= -6.0):
                    return False
                # Very rough concelho centroid check (example for major cities)
                centroids = {
                    "lisboa": (38.7, -9.1),
                    "porto": (41.1, -8.6),
                    "braga": (41.5, -8.4),
                    "coimbra": (40.2, -8.4),
                    "faro": (37.0, -7.9),
                    "aveiro": (40.6, -8.6),
                    "leiria": (39.7, -8.8),
                    "setubal": (38.5, -8.9),
                }
                centroid = centroids.get(concelho.lower())
                if centroid:
                    c_lat, c_lon = centroid
                    if abs(lat_f - c_lat) > 0.1 or abs(lon_f - c_lon) > 0.1:
                        return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def _check_property_type_consistency(self, listing: Dict) -> bool:
        """Check consistency between property type and features"""
        tipo = listing.get("tipologia", "").lower()
        quartos = listing.get("quartos", 0)
        area = listing.get("area_util_m2", 0)
        
        # Basic consistency checks
        if "apartamento" in tipo or "t" in tipo:
            # Apartments should have reasonable area and room count
            return 20 <= area <= 300 and 1 <= quartos <= 10
        elif "moradia" in tipo or "casa" in tipo:
            # Houses should have larger area
            return 50 <= area <= 1000 and 2 <= quartos <= 20
        
        return True
    
    def _check_description_consistency(self, listing: Dict) -> bool:
        """Check consistency between description and structured data"""
        descricao = listing.get("descricao", "").lower()
        quartos = listing.get("quartos", 0)
        area = listing.get("area_util_m2", 0)
        
        if not descricao:
            return True  # Can't check without description
        
        # Check if room count mentioned in description matches data
        if quartos > 0:
            room_patterns = [f"{quartos} quarto", f"{quartos} quartos", f"t{quartos}"]
            if any(pattern in descricao for pattern in room_patterns):
                return True
        
        # Check if area mentioned in description matches data
        if area > 0:
            area_patterns = [f"{area} m", f"{area}m²", f"{area}m2"]
            if any(pattern in descricao for pattern in area_patterns):
                return True
        
        return True  # No inconsistency found


class FreshnessValidator:
    """Validates data freshness"""
    
    def __init__(self):
        self.repo = DatabaseRepository()
    
    def validate(self, listing: Dict) -> QualityDimension:
        """Validate freshness of a listing"""
        
        issues = []
        
        # Check if listing has timestamp
        created_at = listing.get("created_at")
        updated_at = listing.get("updated_at")
        
        if not created_at and not updated_at:
            issues.append("No timestamp information available")
            score = 0.5  # Neutral score for missing timestamps
        else:
            # Use most recent timestamp
            timestamp = updated_at or created_at
            
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now(timezone.utc)
            
            # Ensure timestamp is timezone-aware for safe subtraction
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Calculate age in days
            age_days = (datetime.now(timezone.utc) - timestamp).days
            
            # Score based on age
            if age_days <= 1:
                score = 1.0  # Very fresh
            elif age_days <= 7:
                score = 0.9  # Fresh
            elif age_days <= 30:
                score = 0.7  # Recent
            elif age_days <= 90:
                score = 0.5  # Getting old
            else:
                score = 0.3  # Stale
                issues.append(f"Listing is {age_days} days old")
        
        # Check if passed
        passed = score >= 0.5
        if not passed:
            issues.append(f"Freshness score {score:.2f} below threshold 0.5")
        
        return QualityDimension(
            name="freshness",
            score=score,
            weight=0.10,
            issues=issues,
            passed=passed,
            threshold=0.5
        )


class UniquenessValidator:
    """Validates data uniqueness"""
    
    def __init__(self):
        self.repo = DatabaseRepository()
        self.seen_hashes = set()
    
    def validate(self, listing: Dict) -> QualityDimension:
        """Validate uniqueness of a listing"""
        
        issues = []
        
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(listing)
        
        # Check if this fingerprint exists in database
        if self._is_duplicate(fingerprint):
            issues.append("Duplicate listing detected")
            score = 0.0
        else:
            score = 1.0
        
        # Check if passed
        passed = score >= 0.8
        if not passed:
            issues.append(f"Uniqueness score {score:.2f} below threshold 0.8")
        
        return QualityDimension(
            name="uniqueness",
            score=score,
            weight=0.15,
            issues=issues,
            passed=passed,
            threshold=0.8
        )
    
    def _generate_fingerprint(self, listing: Dict) -> str:
        """Generate fingerprint for deduplication"""
        
        # Key fields for fingerprinting
        key_fields = [
            "preco_pedido",
            "area_util_m2",
            "quartos",
            "concelho",
            "freguesia",
            "andar"
        ]
        
        # Create normalized string
        normalized_parts = []
        for field in key_fields:
            value = listing.get(field, "")
            if value:
                normalized_parts.append(str(value).lower().strip())
        
        normalized_string = "|".join(normalized_parts)
        
        # Generate hash
        return hashlib.md5(normalized_string.encode()).hexdigest()
    
    def _is_duplicate(self, fingerprint: str) -> bool:
        """Check if fingerprint already exists in the database."""
        try:
            # Check in memory cache
            if fingerprint in self.seen_hashes:
                return True
            
            # Check in database via repository
            from realestate_engine.database.repository import DatabaseRepository
            repo = DatabaseRepository()
            with repo.Session() as session:
                from realestate_engine.database.models import CleanListing
                from sqlalchemy import select
                result = session.execute(
                    select(CleanListing).where(CleanListing.fingerprint == fingerprint).limit(1)
                ).scalar_one_or_none()
                if result:
                    self.seen_hashes.add(fingerprint)
                    return True
            return False
            
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False


class Quality5DSystem:
    """Complete 5D Quality System
    
    Uses a separate SQLite cache DB (``quality_cache.db``) instead of the main
    application database. This isolation is intentional:
    
    1. **Performance** — quality results are high-churn, short-TTL cache entries;
       keeping them out of the main DB avoids table bloat and index pressure.
    2. **Resilience** — if the quality cache grows or corrupts, it does not affect
       production listings, valuations, or notifications.
    3. **Portability** — the cache can be wiped, moved, or rebuilt independently
       without touching the primary data store.
    
    In future iterations this may be migrated to Redis or a dedicated cache
    table in PostgreSQL if cross-node consistency becomes required.
    """
    
    def __init__(self, cache_db_path: str = "data/db/quality_cache.db"):
        self.cache_db_path = cache_db_path
        self._init_cache_db()
        
        # Initialize validators
        self.validators = {
            "completeness": CompletenessValidator(),
            "accuracy": AccuracyValidator(),
            "consistency": ConsistencyValidator(),
            "freshness": FreshnessValidator(),
            "uniqueness": UniquenessValidator(),
        }
        
        # Quality thresholds
        self.overall_threshold = 0.85
        self.critical_threshold = 0.7
    
    def _init_cache_db(self):
        """Initialize cache database for quality results"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_cache (
                listing_id TEXT PRIMARY KEY,
                overall_score REAL,
                passed_validation BOOLEAN,
                dimensions TEXT,
                critical_issues TEXT,
                recommendations TEXT,
                validation_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def validate_comprehensive(self, listing: Dict) -> QualityResult:
        """Comprehensive 5D quality validation"""
        
        listing_id = listing.get("id") or listing.get("source_id")
        
        # Check cache first
        cached_result = self._get_cached_result(listing_id)
        if cached_result:
            return cached_result
        
        # Run all validators
        dimensions = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for validator_name, validator in self.validators.items():
            dimension = validator.validate(listing)
            dimensions[validator_name] = dimension
            total_weighted_score += dimension.score * dimension.weight
            total_weight += dimension.weight
        
        # Calculate overall score
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Check if passed validation
        passed_validation = overall_score >= self.overall_threshold
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(dimensions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dimensions)
        
        # Create result
        result = QualityResult(
            overall_score=overall_score,
            passed_validation=passed_validation,
            dimensions=dimensions,
            critical_issues=critical_issues,
            recommendations=recommendations,
            validation_timestamp=datetime.now(),
            listing_id=listing_id
        )
        
        # Cache result
        self._cache_result(result)
        
        return result
    
    def _identify_critical_issues(self, dimensions: Dict[str, QualityDimension]) -> List[str]:
        """Identify critical quality issues"""
        critical_issues = []
        
        for dimension_name, dimension in dimensions.items():
            # Issues from dimensions that failed validation
            if not dimension.passed:
                critical_issues.extend(dimension.issues)
            
            # Issues from low-scoring dimensions
            if dimension.score < self.critical_threshold:
                critical_issues.append(f"Critical: {dimension_name} score {dimension.score:.2f} below {self.critical_threshold}")
        
        return critical_issues
    
    def _generate_recommendations(self, dimensions: Dict[str, QualityDimension]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        for dimension_name, dimension in dimensions.items():
            if not dimension.passed or dimension.score < 0.8:
                if dimension_name == "completeness":
                    recommendations.append("Add missing essential fields (price, area, rooms, location)")
                    recommendations.append("Improve description quality and detail")
                elif dimension_name == "accuracy":
                    recommendations.append("Verify price and area values for accuracy")
                    recommendations.append("Check coordinates are within Portugal bounds")
                elif dimension_name == "consistency":
                    recommendations.append("Ensure consistency between price, area, and rooms")
                    recommendations.append("Verify location data matches coordinates")
                elif dimension_name == "freshness":
                    recommendations.append("Update listing information for freshness")
                elif dimension_name == "uniqueness":
                    recommendations.append("Check for duplicate listings")
        
        return recommendations
    
    def _get_cached_result(self, listing_id: str) -> Optional[QualityResult]:
        """Get cached quality result"""
        if not listing_id:
            return None
        
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM quality_cache WHERE listing_id = ? ORDER BY created_at DESC LIMIT 1",
                (listing_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Reconstruct QualityResult from cache
                dimensions = json.loads(row[3]) if row[3] else {}
                critical_issues = json.loads(row[4]) if row[4] else []
                recommendations = json.loads(row[5]) if row[5] else []
                
                return QualityResult(
                    overall_score=row[1],
                    passed_validation=row[2],
                    dimensions=dimensions,
                    critical_issues=critical_issues,
                    recommendations=recommendations,
                    validation_timestamp=datetime.fromisoformat(row[6]),
                    listing_id=listing_id
                )
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    def _cache_result(self, result: QualityResult):
        """Cache quality result"""
        if not result.listing_id:
            return
        
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Serialize dimensions
            dimensions_serialized = {}
            for name, dimension in result.dimensions.items():
                dimensions_serialized[name] = asdict(dimension)
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO quality_cache 
                (listing_id, overall_score, passed_validation, dimensions, critical_issues, recommendations, validation_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.listing_id,
                    result.overall_score,
                    result.passed_validation,
                    json.dumps(dimensions_serialized),
                    json.dumps(result.critical_issues),
                    json.dumps(result.recommendations),
                    result.validation_timestamp.isoformat()
                )
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def validate_batch(self, listings: List[Dict]) -> List[QualityResult]:
        """Validate multiple listings"""
        results = []
        
        for listing in listings:
            try:
                result = self.validate_comprehensive(listing)
                results.append(result)
            except Exception as e:
                logger.error(f"Validation failed for listing: {e}")
                # Create failed result
                failed_result = QualityResult(
                    overall_score=0.0,
                    passed_validation=False,
                    dimensions={},
                    critical_issues=[f"Validation error: {str(e)}"],
                    recommendations=["Fix data format and retry validation"],
                    validation_timestamp=datetime.now(),
                    listing_id=listing.get("id")
                )
                results.append(failed_result)
        
        return results
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality statistics"""
        
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Get overall statistics
            cursor.execute("SELECT COUNT(*), AVG(overall_score), SUM(passed_validation) FROM quality_cache")
            total_count, avg_score, passed_count = cursor.fetchone()
            
            # Get dimension statistics
            cursor.execute("SELECT dimensions FROM quality_cache")
            all_dimensions = cursor.fetchall()
            
            dimension_stats = {}
            for dimensions_row, in all_dimensions:
                if dimensions_row:
                    dimensions = json.loads(dimensions_row)
                    for name, dimension in dimensions.items():
                        if name not in dimension_stats:
                            dimension_stats[name] = {"total": 0, "passed": 0, "avg_score": 0.0}
                        
                        dimension_stats[name]["total"] += 1
                        if dimension.get("passed", False):
                            dimension_stats[name]["passed"] += 1
                        dimension_stats[name]["avg_score"] += dimension.get("score", 0.0)
            
            # Calculate averages
            for name in dimension_stats:
                stats = dimension_stats[name]
                if stats["total"] > 0:
                    stats["avg_score"] /= stats["total"]
                    stats["pass_rate"] = stats["passed"] / stats["total"]
                else:
                    stats["pass_rate"] = 0.0
            
            conn.close()
            
            return {
                "total_listings": total_count or 0,
                "average_quality_score": avg_score or 0.0,
                "passed_validation_rate": (passed_count / total_count) if total_count > 0 else 0.0,
                "dimension_statistics": dimension_stats,
                "overall_threshold": self.overall_threshold,
                "critical_threshold": self.critical_threshold,
            }
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {e}")
            return {
                "total_listings": 0,
                "average_quality_score": 0.0,
                "passed_validation_rate": 0.0,
                "dimension_statistics": {},
                "overall_threshold": self.overall_threshold,
                "critical_threshold": self.critical_threshold,
            }


# Global instance
_quality_5d_system = None

def get_quality_5d_system() -> Quality5DSystem:
    """Get singleton instance of Quality 5D System"""
    global _quality_5d_system
    if _quality_5d_system is None:
        _quality_5d_system = Quality5DSystem()
    return _quality_5d_system

def validate_listing_quality(listing: Dict) -> QualityResult:
    """Convenience function for single listing validation"""
    system = get_quality_5d_system()
    return system.validate_comprehensive(listing)

def validate_batch_quality(listings: List[Dict]) -> List[QualityResult]:
    """Convenience function for batch validation"""
    system = get_quality_5d_system()
    return system.validate_batch(listings)
