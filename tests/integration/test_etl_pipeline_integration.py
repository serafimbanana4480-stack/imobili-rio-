"""Integration tests for ETL pipeline."""
import pytest
from datetime import datetime, timezone
from realestate_engine.database.models import RawListing, CleanListing
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.etl.normalizer import Normalizer
from realestate_engine.etl.deduplicator import Deduplicator
from realestate_engine.etl.validator import Validator
from realestate_engine.etl.enricher import Enricher
from unittest.mock import MagicMock, patch


class TestETLPipelineIntegration:
    """Integration tests for the full ETL pipeline."""

    @pytest.fixture
    def repo(self, db_repo):
        """Use the database repository fixture."""
        return db_repo

    @pytest.fixture
    def normalizer(self):
        """Normalizer instance."""
        return Normalizer()

    @pytest.fixture
    def deduplicator(self):
        """Deduplicator instance."""
        return Deduplicator()

    @pytest.fixture
    def validator(self):
        """Validator instance."""
        return Validator()

    @pytest.fixture
    def enricher(self):
        """Enricher instance with mocked dependencies."""
        with patch("realestate_engine.etl.enricher.INEClient"), \
             patch("realestate_engine.etl.enricher.POIClient"):
            return Enricher()

    def test_raw_to_clean_listing_flow(self, repo, normalizer, validator):
        """Test flow from raw listing to clean listing."""
        # Create raw listing
        raw = RawListing(
            source_portal="idealista",
            source_id="12345",
            source_url="https://idealista.pt/12345",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={
                "title": "T3 Lisboa",
                "price_text": "350.000 €",
                "area_text": "120 m²",
                "rooms_text": "3 quartos",
            }
        )
        created_raw = repo.create_raw_listing(raw)
        assert created_raw.id is not None

        # Normalize
        normalized = normalizer.normalize(created_raw.raw_data, created_raw.source_portal)
        assert normalized["preco_pedido"] == 350000.0
        assert normalized["area_util_m2"] == 120.0
        assert normalized["quartos"] == 3

        # Validate
        errors = validator.validate(normalized)
        assert len(errors) == 0

        # Create clean listing
        clean = CleanListing(
            source_portal=normalized["source_portal"],
            source_id=normalized["source_id"],
            source_url=normalized["source_url"],
            scrape_timestamp=created_raw.scrape_timestamp,
            titulo=normalized["titulo"],
            preco_pedido=normalized["preco_pedido"],
            area_util_m2=normalized["area_util_m2"],
            quartos=normalized["quartos"],
        )
        created_clean = repo.create_clean_listing(clean)
        assert created_clean.id is not None

    def test_deduplication_flow(self, repo, deduplicator):
        """Test deduplication of similar listings."""
        # Create two similar raw listings
        raw1 = RawListing(
            source_portal="idealista",
            source_id="1",
            source_url="https://idealista.pt/1",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Cedofeita", "price_text": "300.000 €", "area_text": "100 m²"}
        )
        raw2 = RawListing(
            source_portal="imovirtual",
            source_id="2",
            source_url="https://imovirtual.pt/2",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={"title": "T3 Cedofeita", "price_text": "302.000 €", "area_text": "102 m²"}
        )

        repo.create_raw_listings_batch([raw1, raw2])

        # Get existing fingerprints
        existing = repo.get_all_fingerprints() if hasattr(repo, 'get_all_fingerprints') else set()

        # Create normalized listings for deduplication test
        from collections import namedtuple
        Listing = namedtuple("Listing", ["source_portal", "source_id", "freguesia", "tipologia", "area_util_m2", "preco_pedido", "titulo", "lat", "lon"])

        listings = [
            Listing("idealista", "1", "Cedofeita", "T3", 100.0, 300000.0, "T3 Cedofeita", 41.15, -8.61),
            Listing("imovirtual", "2", "Cedofeita", "T3", 102.0, 302000.0, "T3 Cedofeita", 41.15, -8.61),
        ]

        deduped = deduplicator.filter_duplicates(listings, existing)
        assert len(deduped) == 1  # Second should be filtered as duplicate

    def test_batch_validation_flow(self, repo, validator):
        """Test batch validation of multiple listings."""
        listings = [
            {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 3},
            {"preco_pedido": 5000.0, "area_util_m2": 120.0, "quartos": 3},  # Invalid: price too low
            {"preco_pedido": 400000.0, "area_util_m2": 0.0, "quartos": 3},  # Invalid: area is 0
            {"preco_pedido": 380000.0, "area_util_m2": 110.0, "quartos": 3},
        ]

        valid, invalid = validator.validate_batch(listings)
        assert len(valid) == 2
        assert len(invalid) == 2

    @pytest.mark.asyncio
    async def test_enrichment_flow(self, enricher):
        """Test enrichment of listing with external data."""
        listing = {
            "freguesia": "Cedofeita",
            "concelho": "Porto",
            "preco_pedido": 300000.0,
            "area_util_m2": 100.0,
            "titulo": "Apartamento com garagem",
        }
    
        enriched = await enricher.enrich(listing)

        # Check enrichment fields
        assert "ine_preco_medio_m2" in enriched
        assert "ine_tendencia_mensal" in enriched
        assert "preco_por_m2" in enriched
        assert enriched["preco_por_m2"] == 3000.0
        assert enriched["tem_garagem"] is True

    @pytest.mark.asyncio
    async def test_end_to_end_etl_flow(self, repo, normalizer, validator, enricher):
        """Test complete ETL flow from raw to enriched clean listing."""
        # Step 1: Create raw listing
        raw = RawListing(
            source_portal="idealista",
            source_id="99999",
            source_url="https://idealista.pt/99999",
            scrape_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_data={
                "title": "T3 Porto com garagem",
                "price_text": "280.000 €",
                "area_text": "95 m²",
                "rooms_text": "3 quartos",
            }
        )
        repo.create_raw_listing(raw)

        # Step 2: Normalize
        normalized = normalizer.normalize(raw.raw_data, raw.source_portal)
        assert normalized["preco_pedido"] == 280000.0
        assert normalized["area_util_m2"] == 95.0

        # Step 3: Validate
        errors = validator.validate(normalized)
        assert len(errors) == 0

        # Step 4: Enrich
        enriched = await enricher.enrich(normalized)
        assert "preco_por_m2" in enriched
        assert enriched["preco_por_m2"] == 2947.37

        # Step 5: Save as clean listing
        clean = CleanListing(
            source_portal=normalized["source_portal"],
            source_id=normalized["source_id"],
            source_url=normalized["source_url"],
            scrape_timestamp=raw.scrape_timestamp,
            titulo=enriched["titulo"],
            preco_pedido=normalized["preco_pedido"],
            area_util_m2=normalized["area_util_m2"],
            quartos=normalized["quartos"],
            preco_por_m2=enriched.get("preco_por_m2"),
        )
        created_clean = repo.create_clean_listing(clean)
        assert created_clean.id is not None

        # Verify created listing
        assert created_clean.preco_pedido == 280000.0
        assert created_clean.area_util_m2 == 95.0
