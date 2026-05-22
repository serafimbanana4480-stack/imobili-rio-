"""Tests for pagination utility from Phase 6 Dashboard Audit."""
import pytest
import streamlit as st
from realestate_engine.dashboard.utils.pagination import PaginationHandler


class TestPaginationHandler:
    """Test suite for PaginationHandler class."""

    def test_initialization(self):
        """Test PaginationHandler initialization."""
        handler = PaginationHandler(items_per_page=50)
        
        assert handler.items_per_page == 50
        assert handler.MAX_PAGE_SIZE == 200

    def test_initialization_max_page_size(self):
        """Test PaginationHandler respects max page size."""
        handler = PaginationHandler(items_per_page=300)  # Exceeds max
        
        assert handler.items_per_page == 200  # Should be capped

    def test_get_page_data_first_page(self):
        """Test getting first page of data."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=1)
        
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50
        assert page_data[0]["id"] == 0
        assert page_data[-1]["id"] == 9

    def test_get_page_data_second_page(self):
        """Test getting second page of data."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=2)
        
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50
        assert page_data[0]["id"] == 10
        assert page_data[-1]["id"] == 19

    def test_get_page_data_last_page(self):
        """Test getting last page of data."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=5)
        
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50
        assert page_data[0]["id"] == 40
        assert page_data[-1]["id"] == 49

    def test_get_page_data_partial_last_page(self):
        """Test getting last page when it's not full."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(47)]  # Not divisible by 10
        page_data, total_pages, total_items = handler.get_page_data(data, page=5)
        
        assert len(page_data) == 7  # Last page has 7 items
        assert total_pages == 5
        assert total_items == 47

    def test_get_page_data_empty_data(self):
        """Test getting page data with empty dataset."""
        handler = PaginationHandler(items_per_page=10)
        
        data = []
        page_data, total_pages, total_items = handler.get_page_data(data, page=1)
        
        assert len(page_data) == 0
        assert total_pages == 0
        assert total_items == 0

    def test_get_page_data_page_out_of_bounds(self):
        """Test getting page data with page number out of bounds."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=100)
        
        # Should return last page when page exceeds total
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50

    def test_get_page_data_page_zero(self):
        """Test getting page data with page number zero."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=0)
        
        # Should return first page when page is zero
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50

    def test_get_page_data_negative_page(self):
        """Test getting page data with negative page number."""
        handler = PaginationHandler(items_per_page=10)
        
        data = [{"id": i} for i in range(50)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=-1)
        
        # Should return first page when page is negative
        assert len(page_data) == 10
        assert total_pages == 5
        assert total_items == 50

    def test_get_page_data_single_page(self):
        """Test getting page data when data fits in single page."""
        handler = PaginationHandler(items_per_page=50)
        
        data = [{"id": i} for i in range(30)]
        page_data, total_pages, total_items = handler.get_page_data(data, page=1)
        
        assert len(page_data) == 30
        assert total_pages == 1
        assert total_items == 30

    def test_get_cached_data(self):
        """Test get_cached_data utility function."""
        from realestate_engine.dashboard.utils.pagination import get_cached_data
        
        call_count = 0
        
        def fetch_data():
            nonlocal call_count
            call_count += 1
            return [{"id": i} for i in range(10)]
        
        # First call should execute fetch
        result1 = get_cached_data("test_key", fetch_data, ttl=300)
        assert call_count == 1
        assert len(result1) == 10
        
        # Second call should use cache (within TTL)
        result2 = get_cached_data("test_key", fetch_data, ttl=300)
        assert call_count == 1  # Should not increment
        assert len(result2) == 10

    def test_default_page_size(self):
        """Test default page size constant."""
        handler = PaginationHandler()
        
        assert handler.items_per_page == PaginationHandler.DEFAULT_PAGE_SIZE
        assert PaginationHandler.DEFAULT_PAGE_SIZE == 50

    def test_max_page_size_constant(self):
        """Test max page size constant."""
        assert PaginationHandler.MAX_PAGE_SIZE == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
