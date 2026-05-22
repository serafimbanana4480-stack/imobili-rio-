"""Regression test: SQLAlchemy joined eager loads on collections require .unique().

Prevents the bug:
    'The unique() method must be invoked on this Result, as it contains results
     that include joined eager loads against collections'
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))


def test_get_clean_listings_uses_unique():
    """get_clean_listings joins valuations (a collection) so .unique() is required."""
    repo_path = project_root / "realestate_engine" / "database" / "repository.py"
    src = repo_path.read_text(encoding="utf-8")

    # Locate the get_clean_listings function body.
    start = src.index("def get_clean_listings")
    end = src.index("def get_clean_listing_by_source", start)
    body = src[start:end]

    assert "joinedload(CleanListing.valuations)" in body, (
        "get_clean_listings should eager-load valuations"
    )
    assert ".unique().scalars().all()" in body, (
        "get_clean_listings must call .unique() because it joins a collection"
    )


def test_get_top_scores_uses_unique():
    """get_top_scores joins valuations (a collection) so .unique() is required."""
    repo_path = project_root / "realestate_engine" / "database" / "repository.py"
    src = repo_path.read_text(encoding="utf-8")

    start = src.index("def get_top_scores")
    end = src.index("def get_score_by_listing", start)
    body = src[start:end]

    assert "joinedload(CleanListing.valuations)" in body
    assert ".unique().scalars().all()" in body


def test_get_watchlist_uses_unique():
    """get_watchlist joins valuations so .unique() is required."""
    repo_path = project_root / "realestate_engine" / "database" / "repository.py"
    src = repo_path.read_text(encoding="utf-8")

    start = src.index("def get_watchlist")
    end = src.index("def is_in_watchlist", start)
    body = src[start:end]

    assert "joinedload(CleanListing.valuations)" in body
    assert ".unique().scalars().all()" in body
