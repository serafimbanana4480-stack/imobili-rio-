"""Encryption utilities for Real Estate Opportunity Engine."""
import os
from cryptography.fernet import Fernet
from loguru import logger


class EncryptionManager:
    """Manages encryption for sensitive data."""
    
    def __init__(self, key: bytes = None):
        if key is None:
            key_env = os.getenv("ENCRYPTION_KEY")
            if key_env:
                key = key_env.encode()
            else:
                raise RuntimeError(
                    "ENCRYPTION_KEY environment variable is required but not set. "
                    "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
                    "and add it to your .env file."
                )
        self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode())
    
    def decrypt(self, token: bytes) -> str:
        """Decrypt encrypted data."""
        return self.fernet.decrypt(token).decode()
    
    def encrypt_file(self, file_path: str) -> bytes:
        """Encrypt file contents."""
        with open(file_path, "rb") as f:
            return self.fernet.encrypt(f.read())
    
    def decrypt_to_file(self, token: bytes, file_path: str) -> None:
        """Decrypt data to file."""
        with open(file_path, "wb") as f:
            f.write(self.fernet.decrypt(token))
