"""Regression tests for dashboard startup resilience."""
from pathlib import Path


def test_dashboard_app_uses_lazy_view_loading():
    """The dashboard app should lazy-load views instead of importing them eagerly."""
    app_source = Path(__file__).resolve().parents[2] / "realestate_engine" / "dashboard" / "app.py"
    source = app_source.read_text(encoding="utf-8")

    assert "def _render_view" in source
    assert "importlib.import_module" in source
    assert "from realestate_engine.dashboard.views.overview import render_overview" not in source
    assert "from realestate_engine.dashboard.views.search import render_search" not in source


def test_streamlit_file_watcher_is_disabled():
    """Local Streamlit config should disable the file watcher that triggers optional dependency noise."""
    config_file = Path(__file__).resolve().parents[2] / ".streamlit" / "config.toml"
    source = config_file.read_text(encoding="utf-8")

    assert "fileWatcherType = \"none\"" in source
