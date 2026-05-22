"""Validator for ensuring data quality."""
from typing import Dict, List, Any, Tuple
from loguru import logger
import requests
from urllib.parse import urlparse


class Validator:
    """Validates listing data quality."""
    
    REQUIRED_FIELDS = ["preco_pedido", "area_util_m2", "quartos"]
    
    @classmethod
    def validate_url(cls, url: str, timeout: int = 5) -> bool:
        """Check if URL is accessible using HTTP HEAD request."""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            # Use HEAD request to check URL without downloading content
            response = requests.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            # Accept 2xx and 3xx responses as valid
            return 200 <= response.status_code < 400
        except requests.RequestException as e:
            logger.debug(f"URL validation failed for {url}: {e}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error validating URL {url}: {e}")
            return False
    
    @classmethod
    def validate(cls, listing: Dict, validate_url_flag: bool = False) -> List[str]:
        """Validate a listing and return list of errors.
        
        Args:
            listing: Dictionary containing listing data
            validate_url_flag: If True, validate that the URL is accessible
        """
        errors = []
        
        # Reject sample data by default
        if listing.get("is_sample", 0) == 1:
            errors.append("Sample data not allowed in production")
        
        for field in cls.REQUIRED_FIELDS:
            value = listing.get(field)
            if value is None:
                errors.append(f"Missing required field: {field}")
            elif isinstance(value, (int, float)) and value <= 0:
                errors.append(f"Invalid value for {field}: {value}")
        
        # URL validation (optional, can be slow)
        if validate_url_flag:
            url = listing.get("source_url", "")
            if url and not cls.validate_url(url):
                errors.append(f"URL not accessible: {url}")
        
        # Price sanity checks
        preco = listing.get("preco_pedido")
        if preco:
            if preco < 10000:
                errors.append(f"Price too low: {preco}")
            elif preco > 50_000_000:
                errors.append(f"Price too high: {preco}")
        
        # Area sanity checks
        area = listing.get("area_util_m2")
        quartos = listing.get("quartos")
        if area:
            if area < 10:
                errors.append(f"Area too small: {area}")
            elif area > 10_000:
                errors.append(f"Area too large: {area}")
            # Area vs rooms sanity check (detect terrain vs housing)
            elif quartos:
                # T1: >200m² is suspicious (likely terrain)
                if quartos == 1 and area > 200:
                    errors.append(f"Area too large for T1: {area}m² (likely terrain, not housing)")
                # T2: >300m² is suspicious
                elif quartos == 2 and area > 300:
                    errors.append(f"Area too large for T2: {area}m² (likely terrain, not housing)")
                # T3: >400m² is suspicious
                elif quartos == 3 and area > 400:
                    errors.append(f"Area too large for T3: {area}m² (likely terrain, not housing)")
                # T4+: >500m² is suspicious
                elif quartos >= 4 and area > 500:
                    errors.append(f"Area too large for T{quartos}: {area}m² (likely terrain, not housing)")
            # General check: >1000m² is almost certainly terrain
            elif area > 1000:
                errors.append(f"Area extremely large: {area}m² (likely terrain, not housing)")
        
        # Price per m² sanity check
        if preco and area and area > 0:
            p_m2 = preco / area
            if p_m2 < 100:
                errors.append(f"Price/m² too low ({p_m2:.0f}€/m²): possible data error")
            elif p_m2 > 50_000:
                errors.append(f"Price/m² too high ({p_m2:.0f}€/m²): possible data error")
        
        # Rooms sanity checks
        quartos = listing.get("quartos")
        if quartos and (quartos < 0 or quartos > 50):
            errors.append(f"Invalid rooms: {quartos}")
        
        return errors
    
    @classmethod
    def is_valid(cls, listing: Dict) -> bool:
        """Check if listing is valid."""
        return len(cls.validate(listing)) == 0
    
    @classmethod
    def validate_batch(cls, listings: List[Dict], validate_url_flag: bool = False) -> Tuple[List[Dict], List[Dict]]:
        """Validate batch of listings, return (valid, invalid).
        
        Args:
            listings: List of listing dictionaries
            validate_url_flag: If True, validate that URLs are accessible
        """
        valid = []
        invalid = []
        
        for listing in listings:
            errors = cls.validate(listing, validate_url_flag=validate_url_flag)
            if errors:
                listing["_validation_errors"] = errors
                invalid.append(listing)
                logger.warning(f"Invalid listing: {errors}")
            else:
                valid.append(listing)
        
        logger.info(f"Validation: {len(valid)} valid, {len(invalid)} invalid")
        return valid, invalid
