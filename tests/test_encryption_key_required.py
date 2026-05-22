"""Regression test: EncryptionManager must fail loud if ENCRYPTION_KEY missing.

Previously, EncryptionManager auto-generated a key when ENCRYPTION_KEY was
not set, causing encrypted data to become permanently unreadable after a
process restart (the generated key was lost).

Fix: Raise RuntimeError with clear instructions instead of auto-generating.
"""
import os
import pytest

from realestate_engine.security.encryption import EncryptionManager


def test_encryption_manager_raises_when_key_missing(monkeypatch):
    """EncryptionManager must raise RuntimeError when ENCRYPTION_KEY is not set."""
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY environment variable is required"):
        EncryptionManager()


def test_encryption_manager_accepts_valid_key(monkeypatch):
    """EncryptionManager must work when ENCRYPTION_KEY is a valid Fernet key."""
    from cryptography.fernet import Fernet
    valid_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", valid_key)
    mgr = EncryptionManager()
    ciphertext = mgr.encrypt("hello")
    assert mgr.decrypt(ciphertext) == "hello"


def test_encryption_manager_accepts_key_argument():
    """EncryptionManager must accept key passed directly as argument."""
    from cryptography.fernet import Fernet
    valid_key = Fernet.generate_key()
    mgr = EncryptionManager(key=valid_key)
    ciphertext = mgr.encrypt("hello")
    assert mgr.decrypt(ciphertext) == "hello"
