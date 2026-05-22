"""Unit tests for DatabaseRepository."""
import pytest
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import RawListing, CleanListing
from datetime import datetime, timezone


class TestDatabaseRepository:
    """Test database repository functions."""

    def test_init_with_custom_url(self):
        repo = DatabaseRepository(database_url="sqlite:///:memory:")
        assert repo.engine is not None

    def test_init_with_default_url(self):
        repo = DatabaseRepository()
        assert repo.engine is not None

    def test_init_tables(self):
        repo = DatabaseRepository(database_url="sqlite:///:memory:")
        repo.init_tables()
        assert repo.engine is not None

    def test_create_raw_listing(self, db_repo):
        raw = RawListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Lisboa", "price": 350000},
        )
        created = db_repo.create_raw_listing(raw)
        assert created.id is not None
        assert created.source_portal == "idealista"

    def test_create_raw_listings_batch(self, db_repo):
        raws = [
            RawListing(
                source_portal="idealista",
                source_id=str(i),
                source_url=f"https://idealista.pt/{i}",
                scrape_timestamp=datetime.now(timezone.utc).isoformat(),
                raw_data={"title": f"T{i}", "price": i * 100000},
            )
            for i in range(3)
        ]
        created = db_repo.create_raw_listings_batch(raws)
        assert len(created) == 3

    def test_get_raw_listings_no_filter(self, db_repo):
        raw = RawListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Lisboa"},
        )
        db_repo.create_raw_listing(raw)
        
        listings = db_repo.get_raw_listings()
        assert len(listings) >= 1

    def test_get_raw_listings_with_filter(self, db_repo):
        raw = RawListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Lisboa"},
        )
        db_repo.create_raw_listing(raw)
        
        listings = db_repo.get_raw_listings(portal="idealista")
        assert len(listings) >= 1
        assert all(l.source_portal == "idealista" for l in listings)

    def test_get_raw_listing_by_source_id(self, db_repo):
        raw = RawListing(
            source_portal="idealista",
            source_id="99999",
            source_url="https://idealista.pt/99999",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Lisboa"},
        )
        db_repo.create_raw_listing(raw)
        
        found = db_repo.get_raw_listing_by_source_id("idealista", "99999")
        assert found is not None
        assert found.source_id == "99999"

    def test_get_raw_listing_by_source_id_not_found(self, db_repo):
        found = db_repo.get_raw_listing_by_source_id("idealista", "nonexistent")
        assert found is None

    def test_create_clean_listing(self, db_repo):
        clean = CleanListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            titulo="T3 Lisboa",
            preco_pedido=350000.0,
            area_util_m2=120.0,
            quartos=3,
        )
        created = db_repo.create_clean_listing(clean)
        assert created.id is not None
        assert created.preco_pedido == 350000.0

    def test_create_clean_listings_batch(self, db_repo):
        cleans = [
            CleanListing(
                source_portal="idealista",
                source_id=str(i),
                source_url=f"https://idealista.pt/{i}",
                scrape_timestamp=datetime.now(timezone.utc).isoformat(),
                titulo=f"T{i}",
                preco_pedido=float(i * 100000),
                area_util_m2=float(i * 40),
                quartos=i,
            )
            for i in range(1, 4)
        ]
        created = db_repo.create_clean_listings_batch(cleans)
        assert len(created) == 3

    def test_get_clean_listings_with_filters(self, db_repo):
        clean = CleanListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            titulo="T3 Lisboa",
            preco_pedido=350000.0,
            area_util_m2=120.0,
            quartos=3,
            freguesia="Cedofeita",
        )
        db_repo.create_clean_listing(clean)
        
        listings = db_repo.get_clean_listings(filters={"freguesia": "Cedofeita"})
        assert len(listings) >= 1
