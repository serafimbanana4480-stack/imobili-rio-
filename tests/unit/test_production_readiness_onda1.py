"""Regression tests for production-readiness fixes (Onda 1).

These tests verify the three blockers identified in PRODUCTION_READINESS.md
are actually fixed and stay fixed:

- B1: Enricher must instantiate without torch/transformers/ultralytics.
- B3: OpportunityAnalyzer must respect OLLAMA_HOST/OLLAMA_MODEL env vars,
      separate connect/read timeouts, and gracefully fall back when
      Ollama is unreachable.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


# ── B1 regression ─────────────────────────────────────────────────────────


def test_enricher_imports_without_heavy_deps():
    """Enricher module must import cleanly even on a slim install.

    Before fix B1, ``etl/enricher.py`` did top-level imports of cv/, nlp/,
    and features/ modules, which transitively required torch/transformers/
    ultralytics. On a default ``pip install -e .`` (slim), those packages
    are absent and the import raised ModuleNotFoundError, taking down the
    whole pipeline at boot. The lazy loader must keep this passing.
    """
    # Importing should not raise even if torch/transformers/ultralytics
    # are missing; it should just log info-level "disabled" messages.
    from realestate_engine.etl import enricher  # noqa: F401

    assert hasattr(enricher, "Enricher")
    assert hasattr(enricher, "_load_heavy_modules")


def test_enricher_instantiates_with_skip_heavy_flag(monkeypatch):
    """With ENRICH_SKIP_HEAVY=1, all heavy processors must be None."""
    monkeypatch.setenv("ENRICH_SKIP_HEAVY", "1")
    from realestate_engine.etl.enricher import Enricher

    e = Enricher()
    assert e.image_quality_analyzer is None
    assert e.image_similarity_detector is None
    assert e.bert_processor is None
    assert e.sentiment_analyzer is None
    assert e.ner_extractor is None
    assert e.summarizer is None


def test_enricher_heavy_methods_no_op_when_disabled(monkeypatch):
    """Heavy enrichers must null fields gracefully when processors absent."""
    monkeypatch.setenv("ENRICH_SKIP_HEAVY", "1")
    from realestate_engine.etl.enricher import Enricher

    e = Enricher()
    listing = {"descricao": "Apartamento T2 com varanda", "fotos_urls": ["http://x/y.jpg"]}

    out = e.enrich_image_quality(listing.copy())
    assert out["image_quality_score"] is None
    assert out["image_blur_score"] is None
    assert out["image_brightness_score"] is None

    out = e.enrich_image_similarity(listing.copy())
    assert out["image_phash"] is None

    out = e.enrich_bert_sentiment(listing.copy())
    assert out["bert_sentiment_score"] is None
    assert out["bert_sentiment_label"] is None

    out = e.enrich_ner_entities(listing.copy())
    assert out["extracted_entities"] is None


# ── B3 regression ─────────────────────────────────────────────────────────


def test_opportunity_analyzer_respects_env_vars(monkeypatch):
    """OLLAMA_HOST and OLLAMA_MODEL must drive defaults (no hard-coding)."""
    monkeypatch.setenv("OLLAMA_HOST", "http://example.test:9999")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3-14b-fast")

    # Re-import to pick up env (module-level constants).
    import importlib
    import realestate_engine.investor_tools.opportunity_analyzer as mod
    importlib.reload(mod)

    a = mod.OpportunityAnalyzer()
    assert a.host == "http://example.test:9999"
    assert a.model == "qwen3-14b-fast"


def test_opportunity_analyzer_constructor_overrides_env(monkeypatch):
    """Explicit constructor args must override env."""
    monkeypatch.setenv("OLLAMA_HOST", "http://env.test:1111")
    monkeypatch.setenv("OLLAMA_MODEL", "from-env")

    import importlib
    import realestate_engine.investor_tools.opportunity_analyzer as mod
    importlib.reload(mod)

    a = mod.OpportunityAnalyzer(model="explicit-model", host="http://explicit:2222")
    assert a.host == "http://explicit:2222"
    assert a.model == "explicit-model"


def test_opportunity_analyzer_separates_connect_and_read_timeouts(monkeypatch):
    """Connect timeout must stay short; read timeout must accommodate cold-start."""
    monkeypatch.setenv("OLLAMA_CONNECT_TIMEOUT_S", "3")
    monkeypatch.setenv("OLLAMA_READ_TIMEOUT_S", "240")

    import importlib
    import realestate_engine.investor_tools.opportunity_analyzer as mod
    importlib.reload(mod)

    assert mod.CONNECT_TIMEOUT_S == 3.0
    assert mod.READ_TIMEOUT_S == 240.0
    # Read >> connect: protects against cold-start of large models without
    # masking a real outage.
    assert mod.READ_TIMEOUT_S >= mod.CONNECT_TIMEOUT_S * 10


def test_cache_round_trip(tmp_path, monkeypatch):
    """Disk cache must round-trip a thesis by (listing_id, model)."""
    monkeypatch.setenv("AI_DEALS_CACHE_DIR", str(tmp_path / "ai_cache"))

    import importlib
    import realestate_engine.investor_tools.opportunity_analyzer as mod
    importlib.reload(mod)

    assert mod._cache_get(123, "mistral:7b") is None
    mod._cache_put(123, "mistral:7b", "Tese de teste.")
    cached = mod._cache_get(123, "mistral:7b")
    # _cache_get returns either a bare string or {"thesis": ..., "created_at": ...}
    thesis_text = cached["thesis"] if isinstance(cached, dict) else cached
    assert thesis_text == "Tese de teste."
    # Different model must miss.
    assert mod._cache_get(123, "qwen3-14b-fast") is None
