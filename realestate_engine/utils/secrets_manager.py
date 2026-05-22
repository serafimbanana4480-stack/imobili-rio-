"""Secrets manager for production-grade secret handling."""
import os
from typing import Optional
from loguru import logger

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    logger.warning("cryptography not available, secrets will not be encrypted")


class SecretsManager:
    """Manager for handling secrets securely."""
    
    def __init__(self):
        self.encryption_key = os.environ.get("ENCRYPTION_KEY")
        if not self.encryption_key:
            logger.warning("ENCRYPTION_KEY not set, secrets will not be encrypted")
        
        if FERNET_AVAILABLE and self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode())
        else:
            self.cipher = None
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variables.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Secret value or default
        """
        value = os.environ.get(key, default)
        
        if not value and default is None:
            logger.warning(f"Secret {key} not found in environment")
        
        return value
    
    def get_required_secret(self, key: str) -> str:
        """Get required secret, raise error if not found.
        
        Args:
            key: Environment variable name
            
        Returns:
            Secret value
            
        Raises:
            ValueError if secret not found
        """
        value = self.get_secret(key)
        if not value:
            raise ValueError(f"Required secret {key} not found in environment variables")
        return value
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret for storage.
        
        Args:
            secret: Plain text secret
            
        Returns:
            Encrypted secret (base64)
        """
        if not self.cipher:
            logger.warning("Encryption not available, returning plain text")
            return secret
        
        try:
            encrypted = self.cipher.encrypt(secret.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return secret
    
    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret.
        
        Args:
            encrypted: Encrypted secret (base64)
            
        Returns:
            Plain text secret
        """
        if not self.cipher:
            return encrypted
        
        try:
            decrypted = self.cipher.decrypt(encrypted.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted
    
    def validate_jwt_secret(self) -> bool:
        """Validate JWT secret is set and strong enough."""
        jwt_secret = self.get_secret("JWT_SECRET_KEY")
        if not jwt_secret:
            return False
        
        # JWT secret should be at least 32 characters
        if len(jwt_secret) < 32:
            logger.warning("JWT_SECRET_KEY is too short (should be at least 32 characters)")
            return False
        
        return True
    
    def validate_database_secret(self) -> bool:
        """Validate database URL is set."""
        db_url = self.get_secret("DATABASE_URL")
        return db_url is not None


# Singleton instance
secrets_manager = SecretsManager()
