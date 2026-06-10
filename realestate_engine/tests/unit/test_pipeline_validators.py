"""Tests for pipeline-stage validators (Scraping, ETL, CV/NLP, Valuation, Scoring)."""
import pytest
from realestate_engine.pipeline_validators import (
    ScrapingValidator, ETLValidator, CVNLPValidator,
    ValuationValidator, ScoringValidator, PipelineEndToEndValidator
)


def test_scraping_validator_valid_data():
    raw = {
        "price_text": "250000 €",
        "area_text": "85 m²",
        "location": "Cedofeita, Porto",
        "url": "https://idealista.pt/imovel/123",
        "title": "Apartamento T2 em Cedofeita",
    }
    errors = ScrapingValidator.validate(raw)
    assert len(errors) == 0


def test_scraping_validator_missing_price():
    raw = {
        "area_text": "85 m²",
        "location": "Cedofeita, Porto",
        "url": "https://example.com",
        "title": "Test",
    }
    errors = ScrapingValidator.validate(raw)
    assert any("price" in e.lower() for e in errors)


def test_scraping_validator_absurd_price():
    raw = {
        "price_text": "999999999 €",
        "area_text": "85 m²",
        "location": "Cedofeita, Porto",
        "url": "https://example.com",
        "title": "Test",
    }
    errors = ScrapingValidator.validate(raw)
    assert any("absurd" in e.lower() or "high" in e.lower() for e in errors)


def test_scraping_validator_invalid_url():
    raw = {
        "price_text": "250000 €",
        "area_text": "85 m²",
        "location": "Cedofeita, Porto",
        "url": "ftp://invalid",
        "title": "Test",
    }
    errors = ScrapingValidator.validate(raw)
    # ftp is not http/https
    assert any("url" in e.lower() for e in errors)


def test_etl_validator_valid():
    clean = {
        "preco_pedido": 250000.0,
        "area_util_m2": 85.0,
        "lat": 41.15,
        "lon": -8.61,
        "source_portal": "idealista",
        "source_id": "abc123",
        "titulo": "Apartamento T2",
        "ine_preco_medio_m2": 3000.0,
    }
    errors = ETLValidator.validate(clean)
    assert len(errors) == 0


def test_etl_validator_unrealistic_price_m2():
    clean = {
        "preco_pedido": 5000.0,
        "area_util_m2": 100.0,
        "lat": 41.15,
        "lon": -8.61,
        "source_portal": "idealista",
        "source_id": "abc123",
        "titulo": "Apartamento",
    }
    errors = ETLValidator.validate(clean)
    assert any("unrealistic" in e.lower() for e in errors)


def test_etl_validator_outside_portugal():
    clean = {
        "preco_pedido": 250000.0,
        "area_util_m2": 85.0,
        "lat": 51.5,  # London
        "lon": -0.1,
        "source_portal": "idealista",
        "source_id": "abc123",
        "titulo": "Apartamento",
    }
    errors = ETLValidator.validate(clean)
    assert any("coordinates" in e.lower() for e in errors)


def test_etl_validator_batch_duplicates():
    cleans = [
        {"source_id": "dup", "preco_pedido": 100},
        {"source_id": "dup", "preco_pedido": 200},
    ]
    errors = ETLValidator.validate_batch_consistency(cleans)
    assert any("duplicate" in e.lower() for e in errors)


def test_cv_nlp_validator_valid():
    enriched = {
        "image_quality_score": 0.75,
        "bert_sentiment_score": 0.5,
        "bert_sentiment_label": "POSITIVE",
        "description_quality_score": 0.8,
        "ner_entities": [{"label": "LOC", "text": "Porto"}],
    }
    errors = CVNLPValidator.validate(enriched)
    assert len(errors) == 0


def test_cv_nlp_validator_sentiment_mismatch():
    enriched = {
        "bert_sentiment_score": -0.5,
        "bert_sentiment_label": "POSITIVE",
    }
    errors = CVNLPValidator.validate(enriched)
    assert any("POSITIVE" in e for e in errors)


def test_cv_nlp_validator_excessive_entities():
    enriched = {
        "ner_entities": [{"label": "LOC", "text": "Porto"}] * 25,
    }
    errors = CVNLPValidator.validate(enriched)
    assert any("excessive" in e.lower() for e in errors)


def test_valuation_validator_valid():
    valuation = {
        "valor_justo": 260000.0,
        "discount": 0.038,
        "confianca": 0.85,
        "individual_predictions": {
            "hedonic": {"value": 250000.0},
            "comps": {"value": 270000.0},
        }
    }
    listing = {"preco_pedido": 250000.0}
    errors = ValuationValidator.validate(valuation, listing)
    assert len(errors) == 0


def test_valuation_validator_extreme_discount():
    valuation = {
        "valor_justo": 1000000.0,
        "discount": -3.0,  # 300% overpriced (threshold is -2.0)
    }
    listing = {"preco_pedido": 250000.0}
    errors = ValuationValidator.validate(valuation, listing)
    assert any("extreme" in e.lower() for e in errors)


def test_valuation_validator_model_divergence():
    valuation = {
        "valor_justo": 250000.0,
        "individual_predictions": {
            "hedonic": {"value": 100000.0},
            "comps": {"value": 400000.0},
        }
    }
    listing = {"preco_pedido": 250000.0}
    errors = ValuationValidator.validate(valuation, listing)
    assert any("diverge" in e.lower() for e in errors)


def test_scoring_validator_valid():
    score = {
        "score_total": 7.5,
        "score_discount": 8.0,
        "score_location": 7.0,
        "score_condition": 7.0,
        "score_liquidity": 6.0,
        "score_freshness": 8.0,
        "classificacao": "Excelente",
    }
    listing = {"preco_pedido": 200000.0, "valuation_discount": 0.1}
    errors = ScoringValidator.validate(score, listing)
    assert len(errors) == 0


def test_scoring_validator_score_out_of_range():
    score = {
        "score_total": 15.0,
    }
    listing = {"preco_pedido": 200000.0}
    errors = ScoringValidator.validate(score, listing)
    assert any("range" in e.lower() for e in errors)


def test_scoring_validator_inconsistent_high_score():
    score = {
        "score_total": 9.0,
        "score_discount": 3.0,
    }
    listing = {"preco_pedido": 200000.0, "valuation_discount": -0.05}
    errors = ScoringValidator.validate(score, listing)
    assert any("high score" in e.lower() for e in errors)


def test_scoring_validator_classification_mismatch():
    score = {
        "score_total": 5.0,
        "classificacao": "Imperdível",
    }
    listing = {"preco_pedido": 200000.0}
    errors = ScoringValidator.validate(score, listing)
    # Score 5.0 shouldn't be "Imperdível" (needs >= 9.0)
    assert any("Imperdível" in e or "inconsistent" in e.lower() for e in errors)


def test_e2e_validator_complete_pipeline():
    raw = {"price_text": "250000 €", "area_text": "85 m²", "location": "Porto", "url": "http://x", "title": "Apartamento T2"}
    clean = {"preco_pedido": 250000.0, "area_util_m2": 85.0, "lat": 41.15, "lon": -8.61, "source_portal": "x", "source_id": "1", "titulo": "Apartamento T2"}
    enriched = {"image_quality_score": 0.7, "bert_sentiment_score": 0.2, "bert_sentiment_label": "POSITIVE"}
    valuation = {"valor_justo": 260000.0, "discount": 0.04, "confianca": 0.8}
    score = {"score_total": 7.0, "classificacao": "Bom"}

    errors = PipelineEndToEndValidator.validate_complete(raw, clean, enriched, valuation, score)
    assert len(errors) == 0
