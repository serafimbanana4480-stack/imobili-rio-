"""Tests for Deduplicator handling both ORM objects and plain dicts."""
import pytest
from realestate_engine.etl.deduplicator import Deduplicator


class FakeORMListing:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_fingerprint_from_dict():
    listing = {
        "freguesia": "Bonfim",
        "tipologia": "T2",
        "area_util_m2": 85.0,
        "preco_pedido": 250000.0,
        "lat": 41.15,
        "lon": -8.61,
    }
    fp = Deduplicator.generate_fingerprint(listing)
    assert isinstance(fp, str)
    assert len(fp) == 32  # md5 hex


def test_fingerprint_from_orm_object():
    listing = FakeORMListing(
        freguesia="Bonfim",
        tipologia="T2",
        area_util_m2=85.0,
        preco_pedido=250000.0,
        lat=41.15,
        lon=-8.61,
    )
    fp = Deduplicator.generate_fingerprint(listing)
    assert isinstance(fp, str)
    assert len(fp) == 32


def test_filter_duplicates_with_dicts():
    listings = [
        {"freguesia": "Bonfim", "tipologia": "T2", "area_util_m2": 85, "preco_pedido": 250000, "lat": 41.15, "lon": -8.61, "titulo": "A", "source_portal": "idealista"},
        {"freguesia": "Bonfim", "tipologia": "T2", "area_util_m2": 85, "preco_pedido": 250000, "lat": 41.15, "lon": -8.61, "titulo": "B", "source_portal": "imovirtual"},
        {"freguesia": "Foz", "tipologia": "T3", "area_util_m2": 120, "preco_pedido": 450000, "lat": 41.16, "lon": -8.62, "titulo": "C", "source_portal": "idealista"},
    ]
    unique = Deduplicator.filter_duplicates(listings, set())
    assert len(unique) == 2  # first two are duplicates
