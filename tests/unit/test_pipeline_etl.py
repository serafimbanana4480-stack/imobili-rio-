"""Unit tests for PipelineETL."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.database.models import RawListing
from datetime import datetime


class TestPipelineETL:
    """Test ETL pipeline functions."""

    def test_init(self):
        pipeline = PipelineETL()
        assert pipeline.repo is not None
        assert pipeline.normalizer is not None
        assert pipeline.validator is not None
        assert pipeline.deduplicator is not None
        assert pipeline.geocoder is not None
        assert pipeline.enricher is not None

    @pytest.mark.asyncio
    async def test_run_no_listings(self):
        pipeline = PipelineETL()
        with patch.object(pipeline.repo, "get_raw_listings", return_value=[]):
            result = await pipeline.run()
            assert result == 0

    def test_normalizer_integration(self):
        pipeline = PipelineETL()
        raw_data = {
            "title": "T3 Lisboa",
            "price_text": "350.000 €",
            "area_text": "120 m²",
            "rooms_text": "3 quartos",
        }
        normalized = pipeline.normalizer.normalize(raw_data, "idealista")
        assert normalized["preco_pedido"] == 350000.0
        assert normalized["area_util_m2"] == 120.0
        assert normalized["quartos"] == 3
        assert normalized["source_portal"] == "idealista"

    def test_deduplicator_integration(self):
        pipeline = PipelineETL()
        # Create dict-like objects that work with the deduplicator
        from collections import namedtuple
        Listing = namedtuple("Listing", ["source_portal", "source_id", "freguesia", "tipologia", "area_util_m2", "preco_pedido", "titulo", "lat", "lon"])
        
        listings = [
            Listing("idealista", "1", "Cedofeita", "T3", 100.0, 300000.0, "T3 Cedofeita", 41.15, -8.61),
            Listing("imovirtual", "2", "Cedofeita", "T3", 102.0, 302000.0, "T3 Cedofeita", 41.15, -8.61),
        ]
        deduped = pipeline.deduplicator.filter_duplicates(listings, set())
        assert len(deduped) == 1  # Second should be filtered as duplicate

    def test_validator_integration(self):
        pipeline = PipelineETL()
        listings = [
            {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 3},
            {"preco_pedido": 5000.0, "area_util_m2": 120.0, "quartos": 3},
        ]
        valid, invalid = pipeline.validator.validate_batch(listings)
        assert len(valid) == 1
        assert len(invalid) == 1

    @pytest.mark.asyncio
    @patch("realestate_engine.etl.enricher.INEClient")
    @patch("realestate_engine.etl.enricher.POIClient")
    async def test_enricher_integration(self, MockPOI, MockINE):
        mock_ine = MagicMock()
        mock_ine.get_data_for_location.return_value = {
            "median_price": 3000.0,
            "yoy_variation": 12.0
        }
        MockINE.return_value = mock_ine

        mock_poi = MagicMock()
        async def mock_dist(*args, **kwargs): return 500.0
        mock_poi.get_nearest_distance = mock_dist
        MockPOI.return_value = mock_poi

        pipeline = PipelineETL()
        listing = {
            "preco_pedido": 300000.0,
            "area_util_m2": 100.0,
            "freguesia": "Cedofeita",
            "concelho": "Porto",
        }
        enriched = await pipeline.enricher.enrich(listing)
        assert enriched["preco_por_m2"] == 3000.0
        assert "ine_preco_medio_m2" in enriched
