"""Text parsing utilities for real estate data."""
import re
from typing import Optional, Tuple


class TextParsers:
    """Shared text parsing functions for real estate data."""

    # Price patterns
    PRICE_PATTERN = re.compile(r'[\d.,]+\s*[€$]?', re.IGNORECASE)
    PRICE_CLEAN_PATTERN = re.compile(r'[^\d.,]')

    # Area patterns
    AREA_PATTERN = re.compile(r'(\d+[\d.,]*)\s*m[²²]', re.IGNORECASE)
    
    # Room patterns
    ROOM_PATTERN = re.compile(r'(\d+)\s*(?:quartos?|rooms?|bedrooms?)', re.IGNORECASE)
    TYPOLOGY_PATTERN = re.compile(r'[Tt](\d+)', re.IGNORECASE)

    @staticmethod
    def parse_price(price_text: Optional[str]) -> Optional[float]:
        """Parse price from text (e.g., "350.000 €" -> 350000.0)."""
        if not price_text:
            return None
        
        # Extract numeric part
        match = TextParsers.PRICE_PATTERN.search(price_text)
        if not match:
            return None
        
        price_str = match.group()
        
        # Remove currency symbols and keep only digits, dots, and commas
        price_str = TextParsers.PRICE_CLEAN_PATTERN.sub('', price_str)
        
        # Handle Portuguese/European format (1.000.000,00 or 1000000,00)
        # Replace dots with nothing (thousands separator)
        price_str = price_str.replace('.', '')
        # Replace comma with dot (decimal separator)
        price_str = price_str.replace(',', '.')
        
        try:
            return float(price_str)
        except ValueError:
            return None

    @staticmethod
    def parse_area(area_text: Optional[str]) -> Optional[float]:
        """Parse area from text (e.g., "120 m²" -> 120.0)."""
        if not area_text:
            return None
        
        match = TextParsers.AREA_PATTERN.search(area_text)
        if not match:
            return None
        
        try:
            return float(match.group(1).replace(',', '.'))
        except ValueError:
            return None

    @staticmethod
    def parse_rooms(rooms_text: Optional[str]) -> Optional[int]:
        """Parse number of rooms from text (e.g., "3 quartos" -> 3)."""
        if not rooms_text:
            return None
        
        # Try explicit room pattern first
        match = TextParsers.ROOM_PATTERN.search(rooms_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        # Try typology pattern (T3, T2, etc.)
        match = TextParsers.TYPOLOGY_PATTERN.search(rooms_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None

    @staticmethod
    def parse_typology(typology_text: Optional[str]) -> Optional[str]:
        """Parse and normalize typology (e.g., "T3" -> "T3")."""
        if not typology_text:
            return None
        
        match = TextParsers.TYPOLOGY_PATTERN.search(typology_text)
        if match:
            return f"T{match.group(1)}"
        
        return None

    @staticmethod
    def extract_url_id(url: str) -> Optional[str]:
        """Extract ID from URL (last path segment)."""
        if not url:
            return None
        
        # Get last part of URL path
        parts = url.rstrip('/').split('/')
        if parts:
            return parts[-1]
        
        return None

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        """Normalize text by stripping whitespace and lowercasing."""
        if not text:
            return ""
        
        return text.strip().lower()

    @staticmethod
    def extract_phone_number(text: Optional[str]) -> Optional[str]:
        """Extract phone number from text."""
        if not text:
            return None
        
        # Portuguese phone pattern: +351 XXX XXX XXX or 9XX XXX XXX
        pattern = re.compile(r'(\+351\s*)?(\d{3}\s*\d{3}\s*\d{3})')
        match = pattern.search(text)
        
        if match:
            return match.group(0).replace(' ', '')
        
        return None

    @staticmethod
    def parse_energy_cert(cert_text: Optional[str]) -> Optional[str]:
        """Parse energy certificate (A+, A, B, etc.)."""
        if not cert_text:
            return None
        
        cert_text = cert_text.upper().strip()
        
        # Valid energy certificates
        valid_certs = ['A+', 'A-', 'A', 'B-', 'B', 'C', 'D', 'E', 'F', 'G']
        
        for cert in valid_certs:
            if cert in cert_text:
                return cert
        
        return None

    @staticmethod
    def extract_year_from_description(description: Optional[str]) -> Optional[int]:
        """Extract construction year from description text."""
        if not description:
            return None
        
        # Look for patterns like "construído em 2010" or "ano 2015"
        pattern = re.compile(r'(?:constru[íi]do\s*(?:em|no)|ano)\s*(\d{4})', re.IGNORECASE)
        match = pattern.search(description)
        
        if match:
            try:
                year = int(match.group(1))
                # Validate reasonable year range
                if 1800 <= year <= 2026:
                    return year
            except ValueError:
                pass
        
        return None

    @staticmethod
    def extract_floor(text: Optional[str]) -> Optional[int]:
        """Extract floor number from text (e.g., "3º andar" -> 3, "r/c" -> 0)."""
        if not text:
            return None
        
        text = text.lower()
        
        # Check for ground floor variations
        if any(term in text for term in ['r/c', 'rés do chão', 'r/cº']):
            return 0
        
        # Extract floor number
        pattern = re.compile(r'(\d+)[º°ª]\s*(?:andar|piso|floor)', re.IGNORECASE)
        match = pattern.search(text)
        
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None

    @staticmethod
    def clean_address(address: Optional[str]) -> str:
        """Clean and normalize address text."""
        if not address:
            return ""
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address)
        
        # Remove common noise patterns
        noise_patterns = [
            r'\b(?:apartamento|apto?|habitação|moradia|vivenda)\b',
            r'\b(?:à venda|venda|arrendamento|aluguel)\b',
        ]
        
        for pattern in noise_patterns:
            address = re.sub(pattern, '', address, flags=re.IGNORECASE)
        
        return address.strip()
