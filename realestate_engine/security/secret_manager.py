"""Secret manager for secure credential handling.

Provides encrypted storage and retrieval of sensitive configuration
values, replacing plain-text environment variables.
"""
import os
import json
import base64
import hashlib
from typing import Dict, Optional
from pathlib import Path
from loguru import logger

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed; secrets stored in plain text (dev mode)")


class SecretManager:
    """Secure credential store with encryption at rest."""

    def __init__(self, secrets_path: Optional[str] = None, master_key: Optional[str] = None):
        self.secrets_path = secrets_path or os.getenv(
            "REE_SECRETS_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "secrets.enc")
        )
        self.master_key = master_key or os.getenv("REE_MASTER_KEY", "")
        self._secrets: Dict[str, str] = {}
        self._fernet: Optional[Fernet] = None
        self._init_crypto()

    def _init_crypto(self):
        if not CRYPTO_AVAILABLE or not self.master_key:
            self._fernet = None
            return

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"realestate_engine_salt_2026",
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self._fernet = Fernet(key)

    def load(self) -> bool:
        path = Path(self.secrets_path)
        if not path.exists():
            logger.info(f"Secrets file not found at {self.secrets_path}, starting empty")
            return False

        try:
            with open(path, "rb") as f:
                data = f.read()

            if self._fernet:
                data = self._fernet.decrypt(data)

            self._secrets = json.loads(data.decode())
            logger.info(f"Loaded {len(self._secrets)} secrets from {self.secrets_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return False

    def save(self):
        path = Path(self.secrets_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = json.dumps(self._secrets).encode()

        if self._fernet:
            data = self._fernet.encrypt(data)

        with open(path, "wb") as f:
            f.write(data)
        logger.info(f"Saved {len(self._secrets)} secrets to {self.secrets_path}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self._secrets.get(key)
        if value is None:
            value = os.getenv(key, default)
        return value

    def set(self, key: str, value: str):
        self._secrets[key] = value

    def delete(self, key: str):
        self._secrets.pop(key, None)

    def get_all_keys(self) -> list:
        return list(self._secrets.keys())

    def export_env(self) -> Dict[str, str]:
        return dict(self._secrets)


_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
        _secret_manager.load()
    return _secret_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    return get_secret_manager().get(key, default)
