"""Chart components for dashboard."""
import streamlit as st
import pandas as pd


def render_price_histogram(df: pd.DataFrame, column: str = "price_m2"):
    """Render price distribution histogram."""
    if column in df.columns:
        st.bar_chart(df[column].dropna().value_counts().sort_index())


def render_portal_comparison(df: pd.DataFrame):
    """Render portal comparison chart."""
    if "portal" in df.columns and "price" in df.columns:
        chart_data = df.groupby("portal")["price"].mean().sort_values(ascending=False)
        st.bar_chart(chart_data)
