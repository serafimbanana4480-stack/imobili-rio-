"""URL utilities for real estate data."""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin, parse_qs


class URLUtils:
    """Shared URL utility functions."""

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL by ensuring it's absolute and clean."""
        if not url:
            return ""
        
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # Remove fragment
        parsed = urlparse(url)
        clean_url = parsed._replace(fragment='').geturl()
        
        return clean_url

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None

    @staticmethod
    def extract_path(url: str) -> Optional[str]:
        """Extract path from URL."""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            return parsed.path
        except Exception:
            return None

    @staticmethod
    def get_query_param(url: str, param: str) -> Optional[str]:
        """Get query parameter value from URL."""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            values = params.get(param)
            return values[0] if values else None
        except Exception:
            return None

    @staticmethod
    def add_query_param(url: str, param: str, value: str) -> str:
        """Add or update query parameter in URL."""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [value]
            
            # Rebuild query string
            query = '&'.join(f"{k}={v[0]}" for k, v in params.items())
            
            new_url = parsed._replace(query=query).geturl()
            return new_url
        except Exception:
            return url

    @staticmethod
    def extract_listing_id(url: str, patterns: list = None) -> Optional[str]:
        """Extract listing ID from URL using regex patterns."""
        if not url:
            return None
        
        if patterns is None:
            # Default common patterns
            patterns = [
                r'/(\d+)/?$',  # Ends with number
                r'/id(\d+)/?',  # id123
                r'/(\d{6,})/?$',  # Long number (likely ID)
            ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def sanitize_url(url: str) -> str:
        """Remove tracking parameters and clean URL."""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Remove tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'campaign'
            ]
            
            for param in tracking_params:
                params.pop(param, None)
            
            # Rebuild URL without tracking
            if params:
                query = '&'.join(f"{k}={v[0]}" for k, v in params.items())
                clean_url = parsed._replace(query=query).geturl()
            else:
                clean_url = parsed._replace(query='').geturl()
            
            return clean_url
        except Exception:
            return url
