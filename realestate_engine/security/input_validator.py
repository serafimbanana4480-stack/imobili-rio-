"""Input validation and sanitization for Real Estate Opportunity Engine."""
import re
from typing import Optional
from loguru import logger


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    SQL_PATTERN = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)|(--)|(;)|(\bOR\b)|(\bAND\b)", re.IGNORECASE)
    XSS_PATTERN = re.compile(r"(<script)|(javascript:)|(<iframe)|(<object)|(<embed)", re.IGNORECASE)
    
    @staticmethod
    def sanitize_string(value: Optional[str]) -> Optional[str]:
        """Sanitize string input."""
        if not value:
            return value
        value = value.strip()
        value = value.replace("<", "&lt;").replace(">", "&gt;")
        return value
    
    @staticmethod
    def validate_price(value: Optional[float]) -> bool:
        """Validate price."""
        return value is not None and value > 0 and value < 50_000_000
    
    @staticmethod
    def validate_area(value: Optional[float]) -> bool:
        """Validate area in m2."""
        return value is not None and value > 0 and value < 10_000
    
    @staticmethod
    def validate_rooms(value: Optional[int]) -> bool:
        """Validate number of rooms."""
        return value is not None and value >= 0 and value < 50
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for SQL injection patterns."""
        if not value:
            return False
        return bool(cls.SQL_PATTERN.search(value))
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for XSS patterns."""
        if not value:
            return False
        return bool(cls.XSS_PATTERN.search(value))
    
    @classmethod
    def validate_listing_data(cls, data: dict) -> dict:
        """Validate and clean listing data."""
        errors = {}
        for key, value in data.items():
            if isinstance(value, str):
                if cls.check_sql_injection(value):
                    errors[key] = "Potential SQL injection detected"
                if cls.check_xss(value):
                    errors[key] = "Potential XSS detected"
                data[key] = cls.sanitize_string(value)
        return errors
