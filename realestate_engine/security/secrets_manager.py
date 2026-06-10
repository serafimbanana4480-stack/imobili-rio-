"""Secrets management for Real Estate Opportunity Engine."""
import os
from dotenv import load_dotenv
from loguru import logger


class SecretsManager:
    """Manages secrets and sensitive configuration."""
    
    def __init__(self):
        load_dotenv()
    
    def get(self, key: str, default: str = None) -> str:
        """Get secret from environment."""
        value = os.getenv(key, default)
        if value is None:
            logger.warning(f"Secret {key} not found in environment")
        return value
    
    def require(self, key: str) -> str:
        """Get required secret, raise if missing."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required secret {key} not set")
        return value
    
    def mask(self, value: str) -> str:
        """Mask secret for logging."""
        if not value or len(value) <= 8:
            return "***"
        return value[:4] + "****" + value[-4:]
