"""Pagination utility for large datasets in Streamlit dashboard.

Prevents browser crashes when displaying 1000+ listings by implementing
server-side pagination with configurable page sizes.
"""
from typing import List, Dict, Tuple, Any
import streamlit as st
from loguru import logger


class PaginationHandler:
    """Handle pagination for large datasets."""

    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200

    def __init__(self, items_per_page: int = DEFAULT_PAGE_SIZE):
        self.items_per_page = min(items_per_page, self.MAX_PAGE_SIZE)

    def get_page_data(
        self,
        data: List[Dict[str, Any]],
        page: int = 1
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Get data for specific page.

        Args:
            data: Full dataset
            page: Page number (1-indexed)

        Returns:
            Tuple of (page_data, total_pages, total_items)
        """
        total_items = len(data)
        if total_items == 0:
            return [], 0, 0

        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page

        # Validate page number
        page = max(1, min(page, total_pages))

        # Get slice
        start_idx = (page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        page_data = data[start_idx:end_idx]

        return page_data, total_pages, total_items

    def render_pagination_controls(
        self,
        current_page: int,
        total_pages: int,
        key_prefix: str = "pagination"
    ) -> int:
        """Render pagination controls and return selected page.

        Args:
            current_page: Current page number
            total_pages: Total number of pages
            key_prefix: Prefix for Streamlit widget keys

        Returns:
            Selected page number
        """
        if total_pages <= 1:
            return current_page

        # Initialize session state for page if not exists
        page_key = f"{key_prefix}_page"
        if page_key not in st.session_state:
            st.session_state[page_key] = current_page

        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])

        with col1:
            if st.button(
                "⬅️ Anterior",
                disabled=st.session_state[page_key] == 1,
                key=f"{key_prefix}_prev"
            ):
                st.session_state[page_key] = max(1, st.session_state[page_key] - 1)
                st.rerun()

        with col2:
            st.write(f"Página **{st.session_state[page_key]}** de {total_pages}")
            st.caption(f"Total de {total_pages} páginas")

        with col3:
            new_page = st.number_input(
                "Ir para página",
                min_value=1,
                max_value=total_pages,
                value=st.session_state[page_key],
                step=1,
                key=f"{key_prefix}_goto"
            )
            if new_page != st.session_state[page_key]:
                st.session_state[page_key] = new_page
                st.rerun()

        with col4:
            st.caption(f"{self.items_per_page} itens/página")

        with col5:
            if st.button(
                "Próxima ➡️",
                disabled=st.session_state[page_key] == total_pages,
                key=f"{key_prefix}_next"
            ):
                st.session_state[page_key] = min(total_pages, st.session_state[page_key] + 1)
                st.rerun()

        return st.session_state[page_key]

    def render_with_pagination(
        self,
        data: List[Dict[str, Any]],
        key_prefix: str = "pagination"
    ) -> List[Dict[str, Any]]:
        """Render data with pagination controls.

        Args:
            data: Full dataset
            key_prefix: Prefix for Streamlit widget keys

        Returns:
            Data for current page
        """
        total_items = len(data)
        if total_items == 0:
            st.info("Nenhum dado disponível.")
            return []

        # Get current page from session state
        page_key = f"{key_prefix}_page"
        current_page = st.session_state.get(page_key, 1)

        # Get page data
        page_data, total_pages, _ = self.get_page_data(data, current_page)

        # Render info
        st.caption(f"Mostrando {len(page_data)} de {total_items} itens")

        # Render pagination controls
        selected_page = self.render_pagination_controls(current_page, total_pages, key_prefix)

        # Get data for selected page
        page_data, _, _ = self.get_page_data(data, selected_page)

        return page_data


def get_cached_data(cache_key: str, data_fetcher, ttl: int = 300):
    """Get data with caching.

    Args:
        cache_key: Unique key for the cached data
        data_fetcher: Function to fetch data if not cached
        ttl: Time-to-live in seconds (default: 5 minutes)

    Returns:
        Cached or freshly fetched data
    """
    @st.cache_data(ttl=ttl)
    def _fetch():
        return data_fetcher()

    return _fetch()
