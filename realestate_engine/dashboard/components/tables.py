"""Table components for dashboard."""
import streamlit as st
import pandas as pd


def render_listings_table(listings: list):
    """Render listings as interactive table."""
    if not listings:
        st.info("No listings to display.")
        return
    
    df = pd.DataFrame(listings)
    st.dataframe(df, use_container_width=True, hide_index=True)
