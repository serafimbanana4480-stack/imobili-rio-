"""Dashboard theme and styling utilities.

Centralized color palette and styling functions for consistent dashboard appearance.
Includes Plotly theme integration and dark-mode helpers used across all views.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

# Color palette constants
PRIMARY_COLOR = "#1E3A8A"  # Professional blue
PRIMARY_LIGHT = "#1E40AF"  # Lighter blue for hover states
SECONDARY_COLOR = "#10B981"  # Success green
WARNING_COLOR = "#F59E0B"  # Warning orange
ERROR_COLOR = "#EF4444"  # Error red
BACKGROUND_COLOR_LIGHT = "#F8FAFC"  # Light gray background
BACKGROUND_COLOR_DARK = "#0F172A"  # Dark background
SIDEBAR_BACKGROUND = "#1E293B"  # Dark sidebar
TEXT_COLOR_LIGHT = "#1E293B"  # Dark text for light mode
TEXT_COLOR_DARK = "#E2E8F0"  # Light text for dark mode
TEXT_COLOR_MUTED_LIGHT = "#64748B"  # Muted text for light mode
TEXT_COLOR_MUTED_DARK = "#94A3B8"  # Muted text for dark mode
BORDER_COLOR_LIGHT = "#E2E8F0"  # Light border
BORDER_COLOR_DARK = "#334155"  # Dark border

# Profit/loss color scale
PROFIT_STRONG_GREEN = "#16a34a"
PROFIT_GREEN = "#22c55e"
PROFIT_LIGHT_GREEN = "#86efac"
LOSS_STRONG_RED = "#dc2626"
LOSS_RED = "#f87171"
NEUTRAL_GRAY = "#9ca3af"

# Score badge colors
SCORE_HOT = "#dc2626"  # 9.0+
SCORE_EXCELLENT = "#ea580c"  # 7.5-8.9
SCORE_GOOD = "#16a34a"  # 6.0-7.4
SCORE_NEUTRAL = "#6b7280"  # <6.0


def profit_color(lucro_bruto: float) -> str:
    """Return color code based on profit magnitude.
    
    Args:
        lucro_bruto: Gross profit value in EUR
        
    Returns:
        Hex color code string
    """
    if lucro_bruto > 50000:
        return PROFIT_STRONG_GREEN
    elif lucro_bruto > 20000:
        return PROFIT_GREEN
    elif lucro_bruto > 0:
        return PROFIT_LIGHT_GREEN
    elif lucro_bruto < -50000:
        return LOSS_STRONG_RED
    elif lucro_bruto < 0:
        return LOSS_RED
    return NEUTRAL_GRAY


def score_badge(score: float) -> str:
    """Return HTML badge for score.
    
    Args:
        score: Score value (0-10)
        
    Returns:
        HTML string with styled badge
    """
    if score >= 9.0:
        return f'<span style="background:{SCORE_HOT};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;font-weight:bold;">🔥 {score:.1f}</span>'
    elif score >= 7.5:
        return f'<span style="background:{SCORE_EXCELLENT};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;font-weight:bold;">⭐ {score:.1f}</span>'
    elif score >= 6.0:
        return f'<span style="background:{SCORE_GOOD};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;font-weight:bold;">✅ {score:.1f}</span>'
    return f'<span style="background:{SCORE_NEUTRAL};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;">{score:.1f}</span>'


# ── Dark-mode aware helpers ────────────────────────────────────────────────


def is_dark_mode() -> bool:
    """Return True if the dashboard is currently in dark mode."""
    return st.session_state.get("theme", "light") == "dark"


def plotly_layout(**overrides: Any) -> Dict[str, Any]:
    """Return a Plotly layout dict matching the active theme.

    Always pass to ``fig.update_layout(**plotly_layout())`` so charts adapt to
    light/dark mode automatically (dark plotly themes use transparent
    backgrounds + light fonts; light themes use white backgrounds + dark fonts).
    """
    if is_dark_mode():
        base = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": TEXT_COLOR_DARK},
            "xaxis": {"gridcolor": BORDER_COLOR_DARK, "zerolinecolor": BORDER_COLOR_DARK},
            "yaxis": {"gridcolor": BORDER_COLOR_DARK, "zerolinecolor": BORDER_COLOR_DARK},
            "legend": {"font": {"color": TEXT_COLOR_DARK}},
        }
    else:
        base = {
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "font": {"color": TEXT_COLOR_LIGHT},
            "xaxis": {"gridcolor": BORDER_COLOR_LIGHT, "zerolinecolor": BORDER_COLOR_LIGHT},
            "yaxis": {"gridcolor": BORDER_COLOR_LIGHT, "zerolinecolor": BORDER_COLOR_LIGHT},
            "legend": {"font": {"color": TEXT_COLOR_LIGHT}},
        }
    base.update(overrides)
    return base


def apply_theme(fig, **overrides: Any):
    """Apply the active theme to a Plotly figure in-place and return it."""
    fig.update_layout(**plotly_layout(**overrides))
    return fig


def navigate_to_search(filters: Optional[Dict[str, Any]] = None) -> None:
    """Set session-state filters for the Search page and navigate there.

    Used by drill-down chart clicks in Análise: clicking a portal slice or
    typology bar should land the user on Pesquisar with filters pre-applied.
    """
    if filters:
        for key, value in filters.items():
            st.session_state[key] = value
    st.session_state["page"] = "🔍 Pesquisar"
    st.session_state["auto_search"] = True
    st.rerun()
