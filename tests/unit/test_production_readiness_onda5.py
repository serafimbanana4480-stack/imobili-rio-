"""Regression tests for Onda 5 (documentation reconciliation).

Documentation drift was the root cause of `RELATORIO_INCONSISTENCIAS.md`:
the README claimed numbers (8 portals, 22 tests, 4 valuation models, etc.)
that no longer matched the codebase. These tests pin the README claims to
the live codebase counts so CI fails the moment they drift again.

If these tests fail, fix the README (or the codebase) before merging.
Do not relax the assertions.
"""
from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ROOT_README = REPO_ROOT / "README.md"
ENGINE_README = REPO_ROOT / "realestate_engine" / "README.md"


def _count_files(directory: pathlib.Path, pattern: str, exclude: tuple = ()) -> int:
    if not directory.exists():
        return 0
    files = [p for p in directory.glob(pattern) if p.name not in exclude]
    return len(files)


def test_relatorio_inconsistencias_was_archived():
    """The legacy drift report must be replaced by PRODUCTION_READINESS.md."""
    legacy = REPO_ROOT / "RELATORIO_INCONSISTENCIAS.md"
    assert not legacy.exists(), (
        "RELATORIO_INCONSISTENCIAS.md should be deleted after reconciliation. "
        "Use PRODUCTION_READINESS.md instead."
    )
    assert (REPO_ROOT / "PRODUCTION_READINESS.md").exists()


def test_root_readme_quotes_correct_dashboard_view_count():
    """README must state the actual number of Streamlit views (currently 15)."""
    actual_count = _count_files(
        REPO_ROOT / "realestate_engine" / "dashboard" / "views",
        "*.py",
        exclude=("__init__.py",),
    )
    text = ROOT_README.read_text(encoding="utf-8")
    assert f"{actual_count} views Streamlit" in text, (
        f"README must mention '{actual_count} views Streamlit' "
        f"(found {actual_count} files in dashboard/views/)."
    )


def test_root_readme_quotes_correct_spider_count():
    """README must mention 12 spiders (the real count, not 8)."""
    spider_dir = REPO_ROOT / "realestate_engine" / "scraping" / "spiders"
    actual_spiders = len(list(spider_dir.glob("*spider*.py")))
    text = ROOT_README.read_text(encoding="utf-8")
    assert f"{actual_spiders} spiders" in text, (
        f"README must mention '{actual_spiders} spiders' (real count). "
        f"Counted {actual_spiders} *spider*.py files."
    )


def test_root_readme_mentions_macos_section():
    """The README must include a macOS/Linux quick start (it was missing)."""
    text = ROOT_README.read_text(encoding="utf-8").lower()
    assert "macos" in text or "linux" in text, "README missing macOS/Linux section."


def test_root_readme_has_troubleshooting_section():
    """The README must include the Troubleshooting section added in Onda 5."""
    text = ROOT_README.read_text(encoding="utf-8")
    assert "## Troubleshooting" in text, "README missing Troubleshooting section."
    # Each of the 3 most common errors must be addressed.
    assert "OLLAMA" in text.upper() or "ollama" in text
    assert "torch" in text.lower() or "ENRICH_SKIP_HEAVY" in text
    assert "REE_CHROME_PATH" in text or "chrome" in text.lower()


def test_engine_readme_points_to_root_tests_directory():
    """engine/README.md must redirect to the canonical tests/ at repo root."""
    text = ENGINE_README.read_text(encoding="utf-8")
    # Must NOT instruct the reader to run the placeholder paths.
    assert "pytest tests/unit/" not in text, (
        "engine README still points to placeholder tests/unit/. "
        "The canonical suite lives in `tests/` at the repo root."
    )
    assert "raiz" in text.lower(), (
        "engine README must clarify that the real test suite is at the repo root."
    )


def test_no_orphan_references_to_old_test_count():
    """Both READMEs must not claim outdated test numbers (149, 22, 40)."""
    forbidden = ["149/149", "149 testes", "22 passing", "40 testes"]
    for readme in (ROOT_README, ENGINE_README):
        text = readme.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, (
                f"{readme.name} contains stale test count '{needle}'. "
                f"Update to the actual count (29 passing as of Onda 5)."
            )
