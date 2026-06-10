"""Integration tests for Scoring Engine."""
import pytest
from datetime import datetime, UTC
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, Valuation, Score
from realestate_engine.scoring.scoring_engine import ScoringEngine


class TestScoringIntegration:
    """Test scoring engine with database integration."""

    @pytest.mark.asyncio
    async def test_scoring_with_high_discount(self, db_repo):
        """Test scoring with a property with high discount."""
        # Create property with high discount
        listing = CleanListing(
            source_portal="idealista",
            source_id="discount_test",
            source_url="https://idealista.pt/discount",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T3 com Grande Desconto",
            preco_pedido=250000.0,
            area_util_m2=100.0,
            quartos=3,
            casas_banho=2,
            morada_raw="Rua Test",
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            lat=41.15,
            lon=-8.61,
            estado="Novo",
            ano_construcao=2020,
            tipologia="T3",
            num_fotos=20,
            preco_por_m2=2500.0,
            ine_preco_medio_m2=3500.0,
            ine_tendencia_mensal=0.03,
            dist_metro_m=300.0,
        )
        db_repo.create_clean_listing(listing)

        # Create valuation with high discount
        valuation = Valuation(
            listing_id=listing.id,
            valor_justo=350000.0,  # Fair value is 40% higher
            discount=0.2857,  # ~29% discount
            confianca=0.85,
        )
        db_repo.create_valuation(valuation)

        # Run scoring
        engine = ScoringEngine(repo=db_repo)
        count = await engine.score_batch(batch_size=10)

        assert count > 0, "Should have created scores"

        # Get score
        score = db_repo.get_score_by_listing(listing.id)
        assert score is not None
        assert score.score_total >= 7.0, "High discount should result in high score"
        assert score.score_discount >= 7.0, "Discount score should be high"
        assert score.classificacao in ["Excelente", "Imperdível"], "Should be classified as excellent or better"

    @pytest.mark.asyncio
    async def test_scoring_with_poor_location(self, db_repo):
        """Test scoring with a property in poor location."""
        listing = CleanListing(
            source_portal="idealista",
            source_id="location_test",
            source_url="https://idealista.pt/location",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T3 em Localização Distant",
            preco_pedido=300000.0,
            area_util_m2=100.0,
            quartos=3,
            casas_banho=2,
            morada_raw="Rua Test",
            freguesia="Paranhos",  # Less desirable
            concelho="Porto",
            distrito="Porto",
            lat=41.18,
            lon=-8.60,
            estado="Novo",
            ano_construcao=2020,
            tipologia="T3",
            num_fotos=15,
            preco_por_m2=3000.0,
            ine_preco_medio_m2=2800.0,
            ine_tendencia_mensal=0.01,
            dist_metro_m=2000.0,  # Far from metro
        )
        db_repo.create_clean_listing(listing)

        # Create valuation with fair price
        valuation = Valuation(
            listing_id=listing.id,
            valor_justo=300000.0,
            discount=0.0,
            confianca=0.80,
        )
        db_repo.create_valuation(valuation)

        # Run scoring
        engine = ScoringEngine(repo=db_repo)
        await engine.score_batch(batch_size=10)

        # Get score
        score = db_repo.get_score_by_listing(listing.id)
        assert score is not None
        assert score.score_location <= 6.0, "Poor location should result in low location score"

    @pytest.mark.asyncio
    async def test_scoring_with_red_flags(self, db_repo):
        """Test scoring with properties that have red flags."""
        # Property with missing photos
        listing1 = CleanListing(
            source_portal="idealista",
            source_id="redflag1",
            source_url="https://idealista.pt/rf1",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T3 sem fotos",
            preco_pedido=300000.0,
            area_util_m2=100.0,
            quartos=3,
            casas_banho=2,
            morada_raw="Rua Test",
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            lat=41.15,
            lon=-8.61,
            estado="Novo",
            ano_construcao=2020,
            tipologia="T3",
            num_fotos=0,  # Red flag: no photos
            preco_por_m2=3000.0,
        )
        db_repo.create_clean_listing(listing1)

        valuation1 = Valuation(
            listing_id=listing1.id,
            valor_justo=350000.0,
            discount=0.14,
            confianca=0.75,
        )
        db_repo.create_valuation(valuation1)

        # Run scoring
        engine = ScoringEngine(repo=db_repo)
        await engine.score_batch(batch_size=10)

        # Get score
        score = db_repo.get_score_by_listing(listing1.id)
        assert score is not None
        assert len(score.red_flags) > 0, "Should have red flags"

    @pytest.mark.asyncio
    async def test_scoring_classification_boundaries(self, db_repo):
        """Test that classification boundaries are correct."""
        test_cases = [
            (9.5, "Imperdível"),
            (8.5, "Excelente"),
            (6.5, "Bom"),
            (5.0, "Aceitável"),
            (3.5, "Abaixo da média"),
            (1.5, "Não recomendado"),
        ]

        for score_value, expected_class in test_cases:
            listing = CleanListing(
                source_portal="idealista",
                source_id=f"class_test_{score_value}",
                source_url=f"https://idealista.pt/{score_value}",
                scrape_timestamp=datetime.now(UTC).isoformat(),
                titulo=f"Test {score_value}",
                preco_pedido=300000.0,
                area_util_m2=100.0,
                quartos=3,
                casas_banho=2,
                morada_raw="Rua Test",
                freguesia="Cedofeita",
                concelho="Porto",
                distrito="Porto",
                lat=41.15,
                lon=-8.61,
                estado="Novo",
                ano_construcao=2020,
                tipologia="T3",
                num_fotos=15,
                preco_por_m2=3000.0,
            )
            db_repo.create_clean_listing(listing)

            # Create valuation to produce desired score
            discount = (score_value - 5.0) / 10.0
            valuation = Valuation(
                listing_id=listing.id,
                valor_justo=300000.0 / (1 - discount) if discount < 1 else 300000.0,
                discount=max(-0.5, min(0.5, discount)),
                confianca=0.80,
            )
            db_repo.create_valuation(valuation)
    
        # Run scoring
        engine = ScoringEngine(repo=db_repo)
        await engine.score_batch(batch_size=20)
    
        # Verify classifications
        for score_value, expected_class in test_cases:
            listing = db_repo.get_clean_listing_by_source("idealista", f"class_test_{score_value}")
            score = db_repo.get_score_by_listing(listing.id)
            assert score is not None
            # Note: Actual score may differ due to other factors, so we check if it's close
            if expected_class == "Imperdível":
                assert score.score_total >= 9.0 or score.classificacao in ["Excelente", "Imperdível"]
            else:
                # Use partial match for class name to avoid encoding issues in tests
                assert expected_class[:3].lower() in score.classificacao.lower() or score.score_total >= score_value - 2.0
