"""Unit tests for Deduplicator."""
import pytest
from realestate_engine.etl.deduplicator import Deduplicator
from realestate_engine.database.models import CleanListing


class TestDeduplicator:
    """Test deduplicator functions."""

    def test_generate_fingerprint_dict(self):
        listing = {
            "freguesia": "Cedofeita",
            "tipologia": "T3",
            "area_util_m2": 120.0,
            "preco_pedido": 350000.0,
        }
        fp = Deduplicator.generate_fingerprint(listing)
        assert isinstance(fp, str)
        assert len(fp) == 32  # MD5 hex

    def test_generate_fingerprint_same_properties_same_hash(self):
        listing1 = {
            "freguesia": "Cedofeita",
            "tipologia": "T3",
            "area_util_m2": 122.0,  # rounds to 120
            "preco_pedido": 352000.0,  # rounds to 350000
        }
        listing2 = {
            "freguesia": "Cedofeita",
            "tipologia": "T3",
            "area_util_m2": 118.0,  # rounds to 120
            "preco_pedido": 348000.0,  # rounds to 350000
        }
        fp1 = Deduplicator.generate_fingerprint(listing1)
        fp2 = Deduplicator.generate_fingerprint(listing2)
        assert fp1 == fp2

    def test_generate_fingerprint_different_properties_different_hash(self):
        listing1 = {"freguesia": "Cedofeita", "tipologia": "T3", "area_util_m2": 120.0, "preco_pedido": 350000.0}
        listing2 = {"freguesia": "Bonfim", "tipologia": "T3", "area_util_m2": 120.0, "preco_pedido": 350000.0}
        fp1 = Deduplicator.generate_fingerprint(listing1)
        fp2 = Deduplicator.generate_fingerprint(listing2)
        assert fp1 != fp2

    def test_generate_fingerprint_missing_fields(self):
        listing = {"freguesia": "Cedofeita", "tipologia": "T3"}
        fp = Deduplicator.generate_fingerprint(listing)
        assert isinstance(fp, str)
        assert len(fp) == 32

    def test_generate_fingerprint_empty_dict(self):
        listing = {}
        fp = Deduplicator.generate_fingerprint(listing)
        assert isinstance(fp, str)
        assert len(fp) == 32

    def test_generate_fingerprint_case_insensitive_freguesia(self):
        listing1 = {"freguesia": "Cedofeita", "tipologia": "T3", "area_util_m2": 100.0, "preco_pedido": 300000.0}
        listing2 = {"freguesia": "CEDOFEITA", "tipologia": "T3", "area_util_m2": 100.0, "preco_pedido": 300000.0}
        fp1 = Deduplicator.generate_fingerprint(listing1)
        fp2 = Deduplicator.generate_fingerprint(listing2)
        assert fp1 == fp2

    def test_filter_duplicates_empty_list(self):
        result = Deduplicator.filter_duplicates([], set())
        assert result == []

    def test_filter_duplicates_no_duplicates(self):
        listings = [
            type("Obj", (), {"titulo": "A", "source_portal": "idealista", "freguesia": "Cedofeita", "tipologia": "T3", "area_util_m2": 100.0, "preco_pedido": 300000.0})(),
            type("Obj", (), {"titulo": "B", "source_portal": "imovirtual", "freguesia": "Bonfim", "tipologia": "T2", "area_util_m2": 80.0, "preco_pedido": 250000.0})(),
        ]
        result = Deduplicator.filter_duplicates(listings, set())
        assert len(result) == 2

    def test_filter_duplicates_with_existing(self):
        listing = {"freguesia": "Cedofeita", "tipologia": "T3", "area_util_m2": 100.0, "preco_pedido": 300000.0}
        existing_fp = Deduplicator.generate_fingerprint(listing)
        new_listings = [
            type("Obj", (), {"titulo": "A", "source_portal": "idealista", "freguesia": "Cedofeita", "tipologia": "T3", "area_util_m2": 100.0, "preco_pedido": 300000.0})(),
        ]
        result = Deduplicator.filter_duplicates(new_listings, {existing_fp})
        assert len(result) == 0
