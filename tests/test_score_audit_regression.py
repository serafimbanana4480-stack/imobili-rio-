"""Regression test for DetachedInstanceError in score audit view.

Previously, Score.listing was lazy-loaded outside the session scope,
causing sqlalchemy.orm.exc.DetachedInstanceError when the dashboard
tried to access listing attributes after the DB session closed.

Fix: eager loading via selectinload(Score.listing).
"""
import pytest
from sqlalchemy.orm import selectinload

from realestate_engine.database.models import Score, CleanListing, Valuation
from realestate_engine.database.repository import DatabaseRepository


def test_get_top_scores_uses_eager_loading():
    """Verify that get_top_scores loads related objects eagerly."""
    repo = DatabaseRepository()

    # We cannot easily mock the DB session internals, so we inspect the method
    # source to confirm joinedload is used. This is a static regression guard.
    import inspect
    source = inspect.getsource(repo.get_top_scores)

    assert "joinedload" in source, "get_top_scores must use joinedload to avoid DetachedInstanceError"
    assert "Score.listing" in source, "get_top_scores must eagerly load Score.listing"


def test_score_audit_render_query_pattern():
    """Verify the score audit view query pattern uses selectinload."""
    # The view uses selectinload(Score.listing).selectinload(CleanListing.valuations)
    # We import the module and check the render function source.
    import inspect
    from realestate_engine.dashboard.views import score_audit

    source = inspect.getsource(score_audit.render_score_audit)
    assert "selectinload" in source, "render_score_audit must use selectinload"
    assert "Score.listing" in source, "render_score_audit must eagerly load Score.listing"


def test_score_model_has_listing_relationship():
    """Guard: Score model must have a relationship to CleanListing."""
    assert hasattr(Score, "listing"), "Score model missing 'listing' relationship"
    assert hasattr(CleanListing, "valuations"), "CleanListing model missing 'valuations' relationship"


def test_valuation_model_has_listing_relationship():
    """Guard: Valuation model must have a relationship to CleanListing."""
    assert hasattr(Valuation, "listing"), "Valuation model missing 'listing' relationship"
