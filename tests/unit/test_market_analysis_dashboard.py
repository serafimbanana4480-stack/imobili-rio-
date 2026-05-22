"""Regression tests for market analysis dashboard behavior."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd

from realestate_engine.dashboard.views import market_analysis


class _FakeColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSidebar:
    def __init__(self, values):
        self._values = list(values)
        self.calls = []

    def selectbox(self, label, options):
        self.calls.append((label, list(options)))
        return self._values.pop(0)


class _FakeStreamlit:
    def __init__(self, sidebar_values):
        self.sidebar = _FakeSidebar(sidebar_values)
        self.titles = []
        self.metrics = []
        self.markdowns = []
        self.infos = []
        self.warnings = []
        self.dataframes = []
        self.plotly_calls = []

    def info(self, msg):
        self.infos.append(msg)

    def caption(self, msg):
        pass  # Just ignore captions in tests

    def warning(self, msg):
        self.warnings.append(msg)

    def title(self, msg):
        self.titles.append(msg)

    def markdown(self, msg):
        self.markdowns.append(msg)

    def metric(self, *args, **kwargs):
        self.metrics.append((args, kwargs))

    def columns(self, n):
        return [_FakeColumn() for _ in range(n)]

    def tabs(self, labels):
        return [_FakeColumn() for _ in labels]

    def selectbox(self, label, options, index=0):
        # Used inside the freguesia tab
        return options[index]

    def plotly_chart(self, fig, **kwargs):
        self.plotly_calls.append((fig, kwargs))
        return None

    def dataframe(self, df, **kwargs):
        self.dataframes.append((df, kwargs))

    class column_config:
        @staticmethod
        def NumberColumn(*args, **kwargs):
            return (args, kwargs)

        @staticmethod
        def LinkColumn(*args, **kwargs):
            return (args, kwargs)


class _FakeRepo:
    def get_clean_listings(self, limit=10000):
        return [
            SimpleNamespace(
                id="1",
                source_portal="idealista",
                preco_pedido=250000.0,
                area_util_m2=100.0,
                area_bruta_m2=0.0,
                preco_por_m2=2500.0,
                freguesia="Avenidas Novas",
                concelho="Lisboa",
                quartos=3,
                tipologia="T3",
                estado="novo",
                cert_energetico="A+",
                source_url="https://example.com/1",
            ),
        ]


class _FakeINE:
    def __init__(self):
        self._concelho_to_distrito = {"porto": "porto", "lisboa": "lisboa"}
        self._distrito_to_regiao = {"porto": "norte", "lisboa": "lisboa"}
        self.concelhos_data = {
            "porto": {"median_price": 3000.0, "yoy_variation": 1.0, "n_transacoes": 10},
            "lisboa": {"median_price": 5000.0, "yoy_variation": 2.0, "n_transacoes": 20},
        }


def test_handle_chart_click_routes_selected_value(monkeypatch):
    captured = {}

    monkeypatch.setattr(market_analysis, "navigate_to_search", lambda filters: captured.update(filters))

    market_analysis._handle_chart_click(
        {"selection": {"points": [{"x": "T3"}]}} ,
        "tipologia",
        lambda point: point.get("x"),
        lambda value: {"tipologia": value, "min_score": 0.0},
    )

    assert captured == {"tipologia": "T3", "min_score": 0.0}


def test_render_market_analysis_uses_dynamic_title_and_filters(monkeypatch):
    fake_st = _FakeStreamlit(["Lisboa", "Todos"])
    monkeypatch.setattr(market_analysis, "st", fake_st)
    
    # Patch the classes where they are imported (inside the function)
    import realestate_engine.database.repository
    import realestate_engine.valuation.ine_client
    monkeypatch.setattr(realestate_engine.database.repository, "DatabaseRepository", _FakeRepo)
    monkeypatch.setattr(realestate_engine.valuation.ine_client, "INEClient", _FakeINE)
    
    monkeypatch.setattr(market_analysis, "apply_theme", lambda *args, **kwargs: None)
    monkeypatch.setattr(market_analysis, "navigate_to_search", lambda *args, **kwargs: None)
    monkeypatch.setitem(market_analysis.__dict__, "px", SimpleNamespace(
        histogram=lambda *args, **kwargs: MagicMock(),
        pie=lambda *args, **kwargs: MagicMock(),
        bar=lambda *args, **kwargs: MagicMock(),
        scatter=lambda *args, **kwargs: MagicMock(),
        colors=SimpleNamespace(qualitative=SimpleNamespace(Set2=[], Pastel=[])),
    ))
    monkeypatch.setitem(market_analysis.__dict__, "go", SimpleNamespace(Scatter=lambda *args, **kwargs: MagicMock()))
    monkeypatch.setitem(market_analysis.__dict__, "HAS_PLOTLY", True)

    market_analysis.render_market_analysis()

    # Use only ASCII characters for assertions to avoid encoding issues on Windows
    assert any("Mercado" in title and "Lisboa" in title for title in fake_st.titles)
    assert fake_st.sidebar.calls[0][0] == "Região"
    assert fake_st.sidebar.calls[1][0] == "Concelho"
    assert fake_st.dataframes, "Expected INE dataframe to be rendered"
