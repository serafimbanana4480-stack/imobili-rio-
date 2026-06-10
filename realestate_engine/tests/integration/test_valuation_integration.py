"""Integration tests for Valuation Engine."""
import pytest
from datetime import datetime, UTC
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, Valuation
from realestate_engine.valuation.valuation_engine import ValuationEngine


class TestValuationIntegration:
    """Test valuation engine with database integration."""

    @pytest.mark.asyncio
    async def test_valuation_with_realistic_property(self, db_repo):
        """Test valuation with a realistic Porto property."""
        # Create a realistic property
        listing = CleanListing(
            source_portal="idealista",
            source_id="test123",
            source_url="https://idealista.pt/test123",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T3 Renovado em Cedofeita",
            descricao="Apartamento T3 totalmente renovado com vista para o rio",
            preco_pedido=350000.0,
            area_util_m2=120.0,
            quartos=3,
            casas_banho=2,
            morada_raw="Rua de Cedofeita, Porto",
            freguesia="Cedofeita",
            concelho="Porto",
            distrito="Porto",
            lat=41.15,
            lon=-8.61,
            estado="Renovado",
            ano_construcao=2015,
            cert_energetico="B",
            tipologia="T3",
            num_fotos=15,
            preco_por_m2=2916.67,
            ine_preco_medio_m2=3200.0,
            ine_tendencia_mensal=0.02,
            dist_metro_m=500.0,
        )
        db_repo.create_clean_listing(listing)

        # Run valuation
        engine = ValuationEngine(repo=db_repo)
        count = await engine.valuate_batch(batch_size=10)

        assert count > 0, "Should have created valuations"

        # Get valuation
        valuation = db_repo.get_valuation_by_listing(listing.id)
        assert valuation is not None
        assert valuation.valor_justo is not None
        assert valuation.valor_justo > 0
        assert valuation.discount is not None
        assert -1.0 <= valuation.discount <= 1.0
        assert valuation.confianca is not None
        assert 0 <= valuation.confianca <= 1.0

    @pytest.mark.asyncio
    async def test_valuation_edge_cases(self, db_repo):
        """Test valuation with edge cases."""
        test_cases = [
            # Very cheap property
            {
                "preco_pedido": 50000.0,
                "area_util_m2": 30.0,
                "freguesia": "Paranhos",
                "estado": "Usado",
                "ano_construcao": 1980,
            },
            # Very expensive property
            {
                "preco_pedido": 1000000.0,
                "area_util_m2": 200.0,
                "freguesia": "Foz do Douro",
                "estado": "Novo",
                "ano_construcao": 2023,
            },
            # Property without geocoding
            {
                "preco_pedido": 300000.0,
                "area_util_m2": 100.0,
                "freguesia": None,
                "estado": "Bom",
                "ano_construcao": 2000,
                "lat": None,
                "lon": None,
            },
        ]

        for i, case in enumerate(test_cases):
            listing = CleanListing(
                source_portal="idealista",
                source_id=f"edge_case_{i}",
                source_url=f"https://idealista.pt/edge_case_{i}",
                scrape_timestamp=datetime.now(UTC).isoformat(),
                titulo=f"Test Property {i}",
                preco_pedido=case["preco_pedido"],
                area_util_m2=case["area_util_m2"],
                quartos=2,
                casas_banho=1,
                morada_raw="Test Address",
                freguesia=case.get("freguesia"),
                concelho="Porto",
                distrito="Porto",
                lat=case.get("lat"),
                lon=case.get("lon"),
                estado=case["estado"],
                ano_construcao=case["ano_construcao"],
                tipologia="T2",
                preco_por_m2=case["preco_pedido"] / case["area_util_m2"],
            )
            db_repo.create_clean_listing(listing)

        # Run valuation
        engine = ValuationEngine(repo=db_repo)
        count = await engine.valuate_batch(batch_size=10)
    
        assert count == len(test_cases), f"Should create {len(test_cases)} valuations"

    @pytest.mark.asyncio
    async def test_valuation_consistency(self, db_repo):
        """Test that valuation is consistent for similar properties."""
        base_data = {
            "source_portal": "idealista",
            "scrape_timestamp": datetime.now(UTC).isoformat(),
            "titulo": "T3 em Cedofeita",
            "preco_pedido": 350000.0,
            "area_util_m2": 120.0,
            "quartos": 3,
            "casas_banho": 2,
            "morada_raw": "Rua Test",
            "freguesia": "Cedofeita",
            "concelho": "Porto",
            "distrito": "Porto",
            "lat": 41.15,
            "lon": -8.61,
            "estado": "Bom",
            "ano_construcao": 2010,
            "tipologia": "T3",
            "preco_por_m2": 2916.67,
            "ine_preco_medio_m2": 3200.0,
        }

        listing1 = CleanListing(
            **base_data,
            source_id="consistency1",
            source_url="https://idealista.pt/1",
        )
        listing2 = CleanListing(
            **base_data,
            source_id="consistency2",
            source_url="https://idealista.pt/2",
        )

        db_repo.create_clean_listings_batch([listing1, listing2])

        # Run valuation
        engine = ValuationEngine(repo=db_repo)
        await engine.valuate_batch(batch_size=10)

        val1 = db_repo.get_valuation_by_listing(listing1.id)
        val2 = db_repo.get_valuation_by_listing(listing2.id)

        assert val1 is not None
        assert val2 is not None

        difference = abs(val1.valor_justo - val2.valor_justo)
        avg_value = (val1.valor_justo + val2.valor_justo) / 2
        relative_diff = difference / avg_value

        assert relative_diff < 0.1, f"Valuations should be similar: {relative_diff:.2%} difference"

    @pytest.mark.asyncio
    async def test_valuation_exposes_commercial_diagnostics(self, db_repo):
        """Test that valuation output includes business-facing diagnostics."""
        listing = CleanListing(
            source_portal="idealista",
            source_id="diag-test",
            source_url="https://idealista.pt/diag-test",
            scrape_timestamp=datetime.now(UTC).isoformat(),
            titulo="T2 em Paranhos",
            preco_pedido=240000.0,
            area_util_m2=85.0,
            quartos=2,
            casas_banho=1,
            morada_raw="Rua Teste",
            freguesia="Paranhos",
            concelho="Porto",
            distrito="Porto",
            lat=41.17,
            lon=-8.60,
            estado="Bom",
            ano_construcao=2005,
            cert_energetico="C",
            tipologia="T2",
            num_fotos=10,
            preco_por_m2=2823.53,
        )
        db_repo.create_clean_listing(listing)

        engine = ValuationEngine(repo=db_repo)
        result = engine.valuate(
            {
                "preco_pedido": listing.preco_pedido,
                "area_util_m2": listing.area_util_m2,
                "quartos": listing.quartos,
                "casas_banho": listing.casas_banho,
                "freguesia": listing.freguesia,
                "concelho": listing.concelho,
                "distrito": listing.distrito,
                "lat": listing.lat,
                "lon": listing.lon,
                "estado": listing.estado,
                "ano_construcao": listing.ano_construcao,
                "cert_energetico": listing.cert_energetico,
                "tipologia": listing.tipologia,
                "preco_por_m2": listing.preco_por_m2,
            },
            pool=[
                {
                    "preco_pedido": 235000.0,
                    "area_util_m2": 82.0,
                    "quartos": 2,
                    "casas_banho": 1,
                    "freguesia": "Paranhos",
                    "concelho": "Porto",
                    "lat": 41.171,
                    "lon": -8.602,
                    "estado": "Bom",
                    "ano_construcao": 2007,
                    "cert_energetico": "C",
                },
                {
                    "preco_pedido": 248000.0,
                    "area_util_m2": 87.0,
                    "quartos": 2,
                    "casas_banho": 1,
                    "freguesia": "Paranhos",
                    "concelho": "Porto",
                    "lat": 41.169,
                    "lon": -8.598,
                    "estado": "Bom",
                    "ano_construcao": 2004,
                    "cert_energetico": "C",
                },
                {
                    "preco_pedido": 239000.0,
                    "area_util_m2": 84.0,
                    "quartos": 2,
                    "casas_banho": 1,
                    "freguesia": "Paranhos",
                    "concelho": "Porto",
                    "lat": 41.168,
                    "lon": -8.601,
                    "estado": "Bom",
                    "ano_construcao": 2006,
                    "cert_energetico": "C",
                },
            ],
        )

        assert result is not None
        assert "valuation_quality" in result
        assert "value_risk" in result
        assert result["valuation_quality"]["band"] in {"forte", "moderada", "cautelosa"}
        assert result["value_risk"]["label"] in {"baixo", "médio", "alto"}
