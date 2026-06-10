"""Tests for defensive sanitization in PipelineETL.

Validates fixes for:
- Coroutine objects leaking into SQLAlchemy inserts (float/coroutine bug)
- Type coercion for all CleanListing fields
"""
import asyncio
import pytest
from types import coroutine

from realestate_engine.etl.pipeline_etl import _sanitize_value


class FakeCoroutine:
    """Fake coroutine-like object for testing."""
    pass


def test_sanitize_coroutine_returns_none():
    """Coroutine objects must be detected and neutralized."""
    async def _coro(): return 42
    coro = _coro()
    assert _sanitize_value(coro, float, "test_field") is None
    # close coroutine to avoid RuntimeWarning
    coro.close()


def test_sanitize_float_from_int():
    assert _sanitize_value(42, float, "f") == 42.0


def test_sanitize_float_from_string():
    assert _sanitize_value("3.14", float, "f") == 3.14


def test_sanitize_float_invalid_returns_none():
    assert _sanitize_value("abc", float, "f") is None


def test_sanitize_int_from_float():
    assert _sanitize_value(3.9, int, "f") == 3


def test_sanitize_str_from_int():
    assert _sanitize_value(123, str, "f") == "123"


def test_sanitize_none_returns_none():
    assert _sanitize_value(None, float, "f") is None


def test_sanitize_list_unchanged():
    assert _sanitize_value([1, 2, 3], list, "f") == [1, 2, 3]
