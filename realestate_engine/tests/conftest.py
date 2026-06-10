"""Pytest configuration and fixtures.

Uses a shared file-based SQLite database so every component that instantiates
its own DatabaseRepository (Geocoder, Enricher, …) lands on the same tables.
"""
collect_ignore_glob = ["*.txt"]

import os
import tempfile
from pathlib import Path

import pytest
from unittest.mock import patch

from realestate_engine.database.models import Base, init_db
from realestate_engine.database.repository import DatabaseRepository
# Bypass the utils/__init__.py re-export (which shadows the submodule with the
# Config instance) by loading the submodule directly from sys.modules.
import realestate_engine.utils.config  # noqa: F401 — ensures module is loaded
import sys as _sys
config_module = _sys.modules["realestate_engine.utils.config"]


@pytest.fixture(autouse=True)
def mock_poi_client():
    """Mock POIClient globally for all tests (external network call)."""
    with patch("realestate_engine.etl.enricher.POIClient") as mock:
        instance = mock.return_value

        async def mock_dist(*args, **kwargs):
            return 500.0

        instance.get_nearest_distance = mock_dist
        yield instance


@pytest.fixture(scope="function")
def temp_db():
    """Create a file-backed SQLite DB shared across all connections/engines."""
    tmpdir = tempfile.mkdtemp(prefix="re_engine_test_")
    db_path = Path(tmpdir) / "test.db"
    url = f"sqlite:///{db_path.as_posix()}"

    # Point the global config at this DB so Geocoder/Enricher
    # instances that call DatabaseRepository() with no arg agree with
    # the test fixture's explicit repository.
    prev_url = config_module.config.database_url
    config_module.config.database_url = url

    init_db(url)
    try:
        yield url
    finally:
        config_module.config.database_url = prev_url
        try:
            os.remove(db_path)
            os.rmdir(tmpdir)
        except OSError:
            pass


@pytest.fixture(scope="function")
def db_repo(temp_db):
    """Create database repository pointing at the shared test DB."""
    repo = DatabaseRepository(database_url=temp_db)
    repo.init_tables()
    return repo
