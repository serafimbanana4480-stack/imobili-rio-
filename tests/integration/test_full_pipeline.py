"""Integration test for complete pipeline end-to-end.

NO SAMPLE/FAKE DATA. The pipeline is exercised against minimal in-memory raw
listings whose payloads mirror what real spiders produce, but every record is
explicitly created by the test (not by any generate_sample_data helper).

Rules:
  - No import from realestate_engine.utils.generate_sample_data (removed).
  - No is_sample flag (all records behave as real).
  - Empty-DB behaviour is asserted to verify no synthetic fallback exists.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from realestate_engine.database.models import RawListing
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine


def _make_raw_listing(portal: str, source_id: str, *, price: int, area: int,
                     rooms: int, freguesia: str, url: str) -> RawListing:
    """Build a RawListing from a payload that mimics the real spider output."""
    return RawListing(
        source_portal=portal,
        source_id=source_id,
        source_url=url,
        scrape_timestamp=datetime.now(timezone.utc).isoformat(),
        raw_data={
            "source_id": source_id,
            "title": f"Apartamento T{rooms} - {freguesia}",
            "price_text": f"{price:,.0f} €".replace(",", "."),
            "area_text": f"{area} m²",
            "rooms": rooms,
            "location": f"{freguesia}, Porto",
            "description": (
                "Imóvel inserido em zona residencial consolidada, com acessos "
                "diretos a transportes públicos, escolas e comércio."
            ),
            "url": url,
        },
    )


@pytest.fixture
def seeded_raw_listings(db_repo):
    """Seed DB with a handful of realistic RawListing rows (not fakes)."""
    rows = [
        _make_raw_listing("idealista", "idl-0001", price=245000, area=82, rooms=2,
                          freguesia="Cedofeita",
                          url="https://www.idealista.pt/imovel/0000001"),
        _make_raw_listing("imovirtual", "imv-0002", price=310000, area=95, rooms=3,
                          freguesia="Bonfim",
                          url="https://www.imovirtual.pt/anuncio/0000002"),
        _make_raw_listing("casasapo", "csp-0003", price=189000, area=70, rooms=2,
                          freguesia="Paranhos",
                          url="https://casa.sapo.pt/0000003"),
    ]
    db_repo.create_raw_listings_batch(rows)
    return rows


class TestFullPipeline:
    """End-to-end pipeline without any generate_sample_data usage."""

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_database(self, db_repo):
        """Empty DB must not produce any output (no synthetic fallback)."""
        pipeline = PipelineETL(repo=db_repo)
        processed = await pipeline.run()
        assert processed == 0, "ETL must process 0 listings when DB is empty"

        valuation_engine = ValuationEngine(repo=db_repo)
        valuations = await valuation_engine.valuate_batch(batch_size=10)
        assert valuations == 0, "No valuations when no listings"

        scoring_engine = ScoringEngine(repo=db_repo)
        scored = await scoring_engine.score_batch(batch_size=10)
        assert scored == 0, "No scores when no valuations"

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self, db_repo, seeded_raw_listings):
        """Raw -> ETL -> Valuation -> Scoring using real-shape payloads."""
        pipeline = PipelineETL(repo=db_repo)
        processed = await pipeline.run()
        assert processed > 0, "ETL must process the seeded listings"

        clean_listings = db_repo.get_clean_listings(limit=20)
        assert len(clean_listings) > 0

        valuation_engine = ValuationEngine(repo=db_repo)
        valuations_created = await valuation_engine.valuate_batch(batch_size=20)
        assert valuations_created > 0

        for listing in clean_listings:
            valuation = db_repo.get_valuation_by_listing(listing.id)
            assert valuation is not None, f"Missing valuation for {listing.id}"
            assert valuation.valor_justo is not None

        scoring_engine = ScoringEngine(repo=db_repo)
        scored = await scoring_engine.score_batch(batch_size=20)
        assert scored > 0

        for listing in clean_listings:
            score = db_repo.get_score_by_listing(listing.id)
            assert score is not None
            assert 0 <= score.score_total <= 10
            assert score.classificacao

    @pytest.mark.asyncio
    async def test_pipeline_data_integrity(self, db_repo, seeded_raw_listings):
        """Source IDs are preserved end-to-end."""
        pipeline = PipelineETL(repo=db_repo)
        await pipeline.run()

        raw_ids = {r.source_id for r in db_repo.get_raw_listings(limit=10)}
        clean_ids = {c.source_id for c in db_repo.get_clean_listings(limit=10)}
        assert raw_ids == clean_ids, "Source IDs must survive ETL"

        valuation_engine = ValuationEngine(repo=db_repo)
        await valuation_engine.valuate_batch(batch_size=10)

        scoring_engine = ScoringEngine(repo=db_repo)
        await scoring_engine.score_batch(batch_size=10)

        for listing in db_repo.get_clean_listings(limit=10):
            assert db_repo.get_valuation_by_listing(listing.id) is not None
            assert db_repo.get_score_by_listing(listing.id) is not None
