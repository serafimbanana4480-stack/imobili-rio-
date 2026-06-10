"""Integration tests for ETL and database."""
import pytest
from datetime import datetime, UTC

from realestate_engine.database.models import RawListing, CleanListing
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.etl.pipeline_etl import PipelineETL


class TestETLDatabase:
    """Test ETL pipeline with database integration."""
    
    def test_create_raw_listing(self, db_repo):
        raw = RawListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            raw_data={"title": "T3 Lisboa", "price": 350000},
        )
        created = db_repo.create_raw_listing(raw)
        assert created.id is not None
        assert created.source_portal == "idealista"
    
    def test_get_raw_listings(self, db_repo):
        raw = RawListing(
            source_portal="imovirtual",
            source_id="54321",
            source_url="https://imovirtual.pt/54321",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            raw_data={"title": "T2 Porto"},
        )
        db_repo.create_raw_listing(raw)
        
        listings = db_repo.get_raw_listings(portal="imovirtual")
        assert len(listings) == 1
        assert listings[0].source_portal == "imovirtual"
    
    def test_create_clean_listing(self, db_repo):
        clean = CleanListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T3 Lisboa",
            preco_pedido=350000.0,
            area_util_m2=120.0,
            quartos=3,
            freguesia="Avenidas Novas",
            concelho="Lisboa",
        )
        created = db_repo.create_clean_listing(clean)
        assert created.id is not None
        assert created.preco_pedido == 350000.0
