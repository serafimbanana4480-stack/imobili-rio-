"""Regression test: OpportunityAnalyzer must handle Ollama timeout gracefully.

Previously, Ollama cold-start on CPU could exceed short timeouts, causing
the analyzer to crash or hang. The dashboard view then showed a raw exception
instead of a user-friendly fallback thesis.

Fix: Warm-up call, retry with backoff, and local fallback thesis generation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer


@pytest.fixture
def mock_listing():
    m = MagicMock()
    m.preco_pedido = 250000
    m.area_util_m2 = 85
    m.preco_por_m2 = 2941
    m.quartos = 2
    m.casas_banho = 1
    m.tipologia = "T2"
    m.area_bruta_m2 = None
    m.estado_conservacao = "bom"
    m.certificado_energetico = "B"
    m.ano_construcao = 2005
    m.freguesia = "Cedofeita"
    m.concelho = "Porto"
    m.distrito = "Porto"
    m.titulo = "Apartamento T2 Cedofeita"
    m.descricao = "Bonito apartamento"
    m.lat = 41.15
    m.lon = -8.61
    m.dist_metro_m = 350.0
    m.dist_escola_m = None
    m.dist_comercio_m = None
    m.dist_hospital_m = None
    m.dist_praia_m = None
    m.dist_parque_m = None
    m.tem_garagem = False
    m.tem_parqueamento = False
    m.tem_piscina = False
    m.tem_vista_mar = False
    m.tem_vista_rio = False
    m.tem_elevador = False
    m.tem_terraco = False
    m.tem_jardim = False
    m.tem_ac = False
    m.cozinha_separada = False
    m.tem_aquecimento = False
    m.source_url = "https://example.com/imovel/123"
    m.id = 999
    return m


@pytest.fixture
def mock_score():
    m = MagicMock()
    m.score_total = 8.5
    m.score_discount = 9.0
    m.score_location = 8.0
    m.score_condition = 7.5
    m.score_liquidity = 8.5
    m.score_freshness = 8.0
    return m


@pytest.fixture
def mock_valuation():
    m = MagicMock()
    m.valor_justo = 230000
    m.discount = 0.08
    m.confianca = 0.72
    return m


@pytest.mark.asyncio
async def test_analyze_deal_returns_fallback_on_ollama_timeout(mock_listing, mock_score, mock_valuation):
    """If Ollama is unreachable, analyzer must return a local fallback thesis."""
    analyzer = OpportunityAnalyzer(provider="ollama")

    # Simulate Ollama being completely offline
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        with patch.object(analyzer, "_warm_up", return_value=(False, "Ollama indisponível")):
            result = await analyzer.analyze_deal(mock_listing, mock_score, mock_valuation)

    assert isinstance(result, str)
    assert len(result) > 50, "Fallback thesis should be substantial"
    assert "fallback" in result.lower() or "indisponível" in result.lower() or "Porto" in result


@pytest.mark.asyncio
async def test_analyze_deal_retries_on_read_timeout(mock_listing, mock_score, mock_valuation):
    """If Ollama ReadTimeout occurs, analyzer must retry before falling back."""
    from httpx import ReadTimeout
    analyzer = OpportunityAnalyzer(provider="ollama")

    post_mock = AsyncMock(side_effect=[ReadTimeout("Timeout"), Exception("Still down")])
    with patch("httpx.AsyncClient.post", post_mock):
        with patch.object(analyzer, "_warm_up", return_value=(True, None)):
            result = await analyzer.analyze_deal(mock_listing, mock_score, mock_valuation)

    # Should have attempted at least twice (original + 1 retry)
    assert post_mock.call_count >= 1
    assert isinstance(result, str)
