"""Date/time utilities for real estate data."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import re


class DateUtils:
    """Shared date/time utility functions."""

    # Portuguese date patterns
    DATE_PATTERN_PT = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})')
    DATE_PATTERN_ISO = re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})')

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date from string (supports DD/MM/YYYY, YYYY-MM-DD, ISO format)."""
        if not date_str:
            return None
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try Portuguese format DD/MM/YYYY
        match = DateUtils.DATE_PATTERN_PT.search(date_str)
        if match:
            try:
                day, month, year = map(int, match.groups())
                return datetime(year, month, month, day)
            except ValueError:
                pass
        
        # Try YYYY-MM-DD
        match = DateUtils.DATE_PATTERN_ISO.search(date_str)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day)
            except ValueError:
                pass
        
        return None

    @staticmethod
    def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
        """Convert datetime to ISO string."""
        if not dt:
            return None
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.isoformat()

    @staticmethod
    def days_between(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
        """Calculate days between two dates."""
        if not start or not end:
            return None
        
        # Ensure both have timezone
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        
        delta = end - start
        return delta.days

    @staticmethod
    def is_recent(dt: Optional[datetime], days: int = 7) -> bool:
        """Check if date is within specified days from now."""
        if not dt:
            return False
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        delta = now - dt
        
        return delta.days <= days

    @staticmethod
    def parse_relative_time(text: Optional[str]) -> Optional[datetime]:
        """Parse relative time expressions like "há 3 dias", "2 semanas atrás"."""
        if not text:
            return None
        
        text = text.lower()
        now = datetime.now(timezone.utc)
        
        # Pattern: X dias atrás / há X dias
        days_match = re.search(r'(?:há|atrás)?\s*(\d+)\s*dias?', text)
        if days_match:
            days = int(days_match.group(1))
            return now - timedelta(days=days)
        
        # Pattern: X semanas atrás / há X semanas
        weeks_match = re.search(r'(?:há|atrás)?\s*(\d+)\s*semanas?', text)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return now - timedelta(weeks=weeks)
        
        # Pattern: X meses atrás / há X meses
        months_match = re.search(r'(?:há|atrás)?\s*(\d+)\s*meses?', text)
        if months_match:
            months = int(months_match.group(1))
            return now - timedelta(days=months * 30)
        
        # Pattern: hoje
        if 'hoje' in text:
            return now
        
        # Pattern: ontem
        if 'ontem' in text:
            return now - timedelta(days=1)
        
        return None

    @staticmethod
    def format_date(dt: Optional[datetime], format_str: str = "%Y-%m-%d") -> Optional[str]:
        """Format datetime to string."""
        if not dt:
            return None
        
        return dt.strftime(format_str)

    @staticmethod
    def get_age_years(birth_year: Optional[int]) -> Optional[int]:
        """Calculate age in years from birth year."""
        if not birth_year:
            return None
        
        current_year = datetime.now().year
        age = current_year - birth_year
        
        return max(0, age)

    @staticmethod
    def is_valid_year(year: int, min_year: int = 1800, max_year: Optional[int] = None) -> bool:
        """Check if year is within valid range."""
        if max_year is None:
            max_year = datetime.now().year + 1
        
        return min_year <= year <= max_year
