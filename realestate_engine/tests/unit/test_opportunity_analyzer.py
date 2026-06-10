"""Unit tests for the OpportunityAnalyzer AI fallback behavior."""
from datetime import datetime, UTC

import pytest

from realestate_engine.database.models import CleanListing, Score, Valuation
from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer


@pytest.mark.asyncio
async def test_local_fallback_thesis_when_provider_not_implemented():
    """The analyzer should produce a useful thesis even without Ollama."""
    analyzer = OpportunityAnalyzer(provider="local", model="mistral:7b")
    listing = CleanListing(
        source_portal="idealista",
        source_id="ai-fallback-1",
        source_url="https://idealista.pt/ai-fallback-1",
        scrape_timestamp=datetime.now(UTC).isoformat(),
        titulo="T2 no Porto",
        preco_pedido=230000.0,
        area_util_m2=80.0,
        quartos=2,
        casas_banho=1,
        freguesia="Paranhos",
        concelho="Porto",
        distrito="Porto",
        estado="Bom",
        tipologia="T2",
    )
    score = Score(listing_id="ai-fallback-1", score_total=7.8, classificacao="Excelente", rationale="Boa relação preço/localização")
    valuation = Valuation(listing_id="ai-fallback-1", valor_justo=250000.0, discount=0.08, confianca=0.72)

    thesis = await analyzer.analyze_deal(listing, score, valuation)

    assert "Fallback local ativado" in thesis
    assert "buy-to-let" in thesis.lower()
    assert analyzer.last_source == "fallback_local"
    assert analyzer.last_diagnostic["reason"] == "provider_not_implemented"
