"""Unit tests for BestOpportunitySelector profit-aware ranking."""

from types import SimpleNamespace

from realestate_engine.notification.best_opportunity_selector import BestOpportunitySelector


class DummyScore:
    def __init__(self, score_total=8.0, score_location=7.0, score_condition=7.0, red_flags=None):
        self.score_total = score_total
        self.score_location = score_location
        self.score_condition = score_condition
        self.red_flags = red_flags or []


class DummyValuation:
    def __init__(self, valor_justo, discount=0.15, confianca=0.8):
        self.valor_justo = valor_justo
        self.discount = discount
        self.confianca = confianca


class DummyListing:
    def __init__(self, preco_pedido, area_util_m2=100.0, freguesia="Cedofeita", concelho="Porto", estado="Bom"):
        self.id = "listing-1"
        self.preco_pedido = preco_pedido
        self.area_util_m2 = area_util_m2
        self.freguesia = freguesia
        self.concelho = concelho
        self.estado = estado
        self.ano_renovacao = None
        self.descricao = "Apartamento em bom estado"
        self.ine_tendencia_mensal = 0.02
        self.valuations = [DummyValuation(valor_justo=preco_pedido * 1.2)]


def test_composite_score_uses_risk_adjusted_profit(monkeypatch):
    selector = BestOpportunitySelector()
    listing = DummyListing(preco_pedido=250000.0)
    score = DummyScore()

    monkeypatch.setattr(
        "realestate_engine.notification.best_opportunity_selector.InvestorTools.calculate_deal_profit",
        lambda **kwargs: {"risk_adjusted_profit": 100000.0},
    )

    composite = selector._calculate_composite_score(listing, score)

    assert composite > 0
    assert composite >= 8.0


def test_verify_realism_rejects_negative_adjusted_profit(monkeypatch):
    selector = BestOpportunitySelector()
    listing = DummyListing(preco_pedido=250000.0)
    score = DummyScore()

    monkeypatch.setattr(
        "realestate_engine.notification.best_opportunity_selector.InvestorTools.calculate_deal_profit",
        lambda **kwargs: {"risk_adjusted_profit": -5000.0},
    )

    assert selector._verify_realism(listing, score) is False
