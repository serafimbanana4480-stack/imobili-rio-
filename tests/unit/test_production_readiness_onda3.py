"""Regression tests for Onda 3 (UI dark-mode contrast).

The user's primary surface is dark. Streamlit's `st.dataframe` is rendered
on a HTML <canvas> by glide-data-grid which IGNORES CSS overrides; the only
way to make those table cells dark is via `.streamlit/config.toml` `[theme]
base = "dark"`. If someone reverts that to "light", every dataframe in the
app silently becomes a glaring white block on the dark page background -
exactly the bug the user reported in the screenshot.

This test fails loudly on regression.
"""
from __future__ import annotations

import pathlib
import re
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def test_streamlit_theme_is_dark():
    cfg = REPO_ROOT / ".streamlit" / "config.toml"
    assert cfg.exists(), f"Missing {cfg}"
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    theme = data.get("theme", {})
    assert theme.get("base") == "dark", (
        "`.streamlit/config.toml` [theme] base must be 'dark' so st.dataframe "
        "(canvas-rendered) shows dark cells. Reverting to 'light' makes all "
        "tables unreadable on the dark page background."
    )
    # Background and text must contrast.
    assert theme.get("backgroundColor", "").lower() in {"#0f172a", "#0b1220"}
    assert theme.get("textColor", "").lower() in {"#e2e8f0", "#f1f5f9"}


def test_overview_view_uses_dark_text_colors():
    """overview.py must not hardcode TEXT_COLOR_MUTED_LIGHT (cinza-escuro).

    Those colours are designed for light-mode pages; on a dark page
    background they become near-invisible. Onda 3 swapped them for the
    DARK variants. This test prevents accidental reintroduction.
    """
    src = (REPO_ROOT / "realestate_engine" / "dashboard" / "views" / "overview.py").read_text(encoding="utf-8")
    assert "TEXT_COLOR_MUTED_LIGHT" not in src, (
        "overview.py must use TEXT_COLOR_MUTED_DARK (visible on dark bg)."
    )
    # The light-text constant is also banned in this view.
    assert not re.search(r"\bTEXT_COLOR_LIGHT\b", src), (
        "overview.py must use TEXT_COLOR_DARK (visible on dark bg)."
    )


def test_no_hardcoded_light_card_backgrounds_in_dashboard_views():
    """Dashboard views must not hardcode #f3f4f6 / #f8fafc / white card bgs.

    Those create blinding light blocks inside dark cards. Use #0F172A or
    #1E293B variants instead.
    """
    views_dir = REPO_ROOT / "realestate_engine" / "dashboard" / "views"
    offenders: list[str] = []
    banned = (
        "background:#f3f4f6",
        "background:#f8fafc",
        "background:#FFFFFF",
        "background: white",
    )
    for py in views_dir.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for needle in banned:
            if needle.lower() in text.lower():
                offenders.append(f"{py.name}: contains '{needle}'")
    assert not offenders, (
        "Hard-coded light backgrounds detected (will be unreadable in dark "
        "mode):\n  - " + "\n  - ".join(offenders)
    )
