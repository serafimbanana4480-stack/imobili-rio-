"""Pipeline-stage data validators for end-to-end quality assurance.

Implements validation rules for each layer:
- Scraping: price, area, location, URL validity
- ETL: normalization correctness, deduplication, coordinate validity
- CV/NLP: score ranges, sentiment coherence, entity relevance
- Valuation: model consistency, reasonable discount ranges
- Scoring: coherent scores, no absurd outliers

Usage:
    from realestate_engine.pipeline_validators import ScrapingValidator, ETLValidator, ...
    errors = ScrapingValidator.validate(raw_dict)
"""
import re
from typing import Dict, List, Optional, Any
from statistics import median, stdev
from loguru import logger


class ScrapingValidator:
    """Validate raw scraped data before ETL ingestion."""

    @classmethod
    def validate(cls, raw: Dict[str, Any]) -> List[str]:
        errors = []

        # Price validation
        price_text = raw.get("price_text") or raw.get("preco") or raw.get("price")
        price = cls._extract_number(price_text)
        if price is None:
            errors.append("SCRAPING: missing or unparseable price")
        elif price <= 0:
            errors.append(f"SCRAPING: invalid price {price}")
        elif price < 10_000:
            errors.append(f"SCRAPING: price suspiciously low {price}")
        elif price > 50_000_000:
            errors.append(f"SCRAPING: price absurdly high {price}")

        # Area validation
        area_text = raw.get("area_text") or raw.get("area") or raw.get("area_util")
        area = cls._extract_number(area_text)
        if area is None:
            errors.append("SCRAPING: missing or unparseable area")
        elif area <= 0:
            errors.append(f"SCRAPING: invalid area {area}")
        elif area < 10:
            errors.append(f"SCRAPING: area too small {area}m²")
        elif area > 10_000:
            errors.append(f"SCRAPING: area too large {area}m²")

        # Location validation
        location = raw.get("location") or raw.get("address") or raw.get("morada")
        if not location or len(str(location).strip()) < 5:
            errors.append("SCRAPING: location too short or missing")

        # URL validation
        url = raw.get("url") or raw.get("source_url")
        if not url:
            errors.append("SCRAPING: missing URL")
        elif not str(url).startswith(("http://", "https://")):
            errors.append(f"SCRAPING: invalid URL scheme {url}")

        # Title validation
        title = raw.get("title") or raw.get("titulo")
        if not title or len(str(title).strip()) < 5:
            errors.append("SCRAPING: title too short")

        return errors

    @classmethod
    def is_valid(cls, raw: Dict[str, Any]) -> bool:
        return len(cls.validate(raw)) == 0

    @staticmethod
    def _extract_number(text) -> Optional[float]:
        if text is None:
            return None
        text = str(text)
        # Remove currency, units, spaces
        cleaned = re.sub(r"[^\d.,]", "", text)
        if not cleaned:
            return None
        # Handle European format
        if "," in cleaned and "." not in cleaned:
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned and "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None


class ETLValidator:
    """Validate normalized/clean listing data after ETL."""

    @classmethod
    def validate(cls, clean: Dict[str, Any]) -> List[str]:
        errors = []

        # Numeric consistency
        preco = clean.get("preco_pedido")
        area = clean.get("area_util_m2")
        if preco and area and area > 0:
            p_m2 = preco / area
            if p_m2 < 100:
                errors.append(f"ETL: price/m² unrealistic {p_m2:.0f}€/m²")
            elif p_m2 > 50_000:
                errors.append(f"ETL: price/m² unrealistic {p_m2:.0f}€/m²")

        # Coordinate validity (Porto region roughly)
        lat = clean.get("lat")
        lon = clean.get("lon")
        if lat is not None and lon is not None:
            if not (36 < lat < 43 and -10 < lon < -5):
                errors.append(f"ETL: coordinates outside Portugal ({lat}, {lon})")

        # Required fields presence
        for field in ["source_portal", "source_id", "titulo"]:
            if not clean.get(field):
                errors.append(f"ETL: missing required field '{field}'")

        # Deduplication marker
        fingerprint = clean.get("_fingerprint")
        if fingerprint and len(str(fingerprint)) != 32:
            errors.append("ETL: invalid fingerprint format")

        # INE enrichment sanity
        ine_m2 = clean.get("ine_preco_medio_m2")
        if ine_m2 and (ine_m2 < 500 or ine_m2 > 20000):
            errors.append(f"ETL: INE price/m² suspicious {ine_m2}")

        return errors

    @classmethod
    def validate_batch_consistency(cls, cleans: List[Dict[str, Any]]) -> List[str]:
        """Cross-listing consistency checks (duplicates, outliers)."""
        errors = []
        if not cleans:
            return errors

        # Duplicate source_ids
        ids = [c.get("source_id") for c in cleans if c.get("source_id")]
        if len(ids) != len(set(ids)):
            dupes = [x for x in ids if ids.count(x) > 1]
            errors.append(f"ETL: duplicate source_ids found: {set(dupes)}")

        # Price outlier detection (IQR)
        prices = [c["preco_pedido"] for c in cleans if c.get("preco_pedido")]
        if len(prices) >= 10:
            prices_sorted = sorted(prices)
            n = len(prices_sorted)
            q1 = prices_sorted[n // 4]
            q3 = prices_sorted[(n * 3) // 4]
            iqr = q3 - q1
            lower = q1 - 3.0 * iqr
            upper = q3 + 3.0 * iqr
            outliers = [p for p in prices if p < lower or p > upper]
            if outliers:
                errors.append(f"ETL: {len(outliers)} price outliers detected (IQR method)")

        return errors


class CVNLPValidator:
    """Validate computer vision and NLP enrichment outputs."""

    @classmethod
    def validate(cls, enriched: Dict[str, Any]) -> List[str]:
        errors = []

        # Image quality score range
        img_score = enriched.get("image_quality_score")
        if img_score is not None and not (0 <= img_score <= 1):
            errors.append(f"CV/NLP: image_quality_score out of range {img_score}")

        # Sentiment coherence
        sentiment = enriched.get("bert_sentiment_score")
        label = enriched.get("bert_sentiment_label")
        if sentiment is not None:
            if not (-1 <= sentiment <= 1):
                errors.append(f"CV/NLP: sentiment score out of range {sentiment}")
            # Label must match score sign
            if label == "POSITIVE" and sentiment < -0.1:
                errors.append(f"CV/NLP: POSITIVE label with negative score {sentiment}")
            elif label == "NEGATIVE" and sentiment > 0.1:
                errors.append(f"CV/NLP: NEGATIVE label with positive score {sentiment}")

        # Description quality
        desc_score = enriched.get("description_quality_score")
        if desc_score is not None and not (0 <= desc_score <= 1):
            errors.append(f"CV/NLP: description_quality_score out of range {desc_score}")

        # NER entities sanity
        entities = enriched.get("ner_entities", [])
        if isinstance(entities, list):
            loc_entities = [e for e in entities if isinstance(e, dict) and e.get("label") == "LOC"]
            if len(loc_entities) > 20:
                errors.append(f"CV/NLP: excessive location entities {len(loc_entities)}")

        return errors


class ValuationValidator:
    """Validate valuation model outputs."""

    @classmethod
    def validate(cls, valuation: Dict[str, Any], listing: Dict[str, Any]) -> List[str]:
        errors = []

        preco = listing.get("preco_pedido", 0)
        valor_justo = valuation.get("valor_justo")

        if valor_justo is None or valor_justo <= 0:
            errors.append("VALUATION: missing or invalid fair value")
            return errors

        # Discount sanity
        discount = valuation.get("discount")
        if discount is not None:
            if discount < -2.0:  # >200% overpriced
                errors.append(f"VALUATION: extreme overpricing {discount:.0%}")
            elif discount > 1.0:  # >100% underpriced (suspicious)
                errors.append(f"VALUATION: extreme underpricing {discount:.0%}")

        # Confidence range
        conf = valuation.get("confianca")
        if conf is not None and not (0 <= conf <= 1):
            errors.append(f"VALUATION: confidence out of range {conf}")

        # Model consistency (individual predictions should not diverge wildly)
        individual = valuation.get("individual_predictions", {})
        preds = [v["value"] for v in individual.values() if isinstance(v, dict) and v.get("value")]
        if len(preds) >= 2:
            m = median(preds)
            spread = max(preds) - min(preds)
            if m > 0 and spread / m > 1.0:  # >100% spread
                errors.append(f"VALUATION: model predictions diverge >100% (spread={spread:.0f})")

        return errors

    @classmethod
    def validate_batch_consistency(cls, valuations: List[Dict[str, Any]]) -> List[str]:
        errors = []
        if len(valuations) < 2:
            return errors

        discounts = [v.get("discount") for v in valuations if v.get("discount") is not None]
        if discounts:
            mean_d = sum(discounts) / len(discounts)
            if mean_d < -0.5:
                errors.append("VALUATION: batch heavily overpriced on average")
            elif mean_d > 0.5:
                errors.append("VALUATION: batch heavily underpriced on average")

        return errors


class ScoringValidator:
    """Validate final scoring outputs."""

    @classmethod
    def validate(cls, score: Dict[str, Any], listing: Dict[str, Any]) -> List[str]:
        errors = []

        total = score.get("score_total")
        if total is None:
            errors.append("SCORING: missing total score")
        elif not (0 <= total <= 10):
            errors.append(f"SCORING: total score out of range {total}")

        # Score coherence with listing data
        preco = listing.get("preco_pedido", 0)
        discount = listing.get("valuation_discount") or score.get("score_discount")

        if preco and discount is not None:
            # High score should correlate with positive discount (underpriced)
            if total >= 8.0 and discount <= 0:
                errors.append(f"SCORING: high score {total} but no discount detected")

        # Component scores should sum reasonably
        components = [
            score.get("score_discount"),
            score.get("score_location"),
            score.get("score_condition"),
            score.get("score_liquidity"),
            score.get("score_freshness"),
        ]
        valid_components = [c for c in components if c is not None]
        if valid_components:
            avg_component = sum(valid_components) / len(valid_components)
            if abs(total - avg_component) > 3.0:
                errors.append(f"SCORING: total score {total} inconsistent with components avg {avg_component:.1f}")

        # Classification coherence
        classification = score.get("classificacao")
        if classification and total is not None:
            expected = cls._expected_classification(total)
            if classification != expected and total < 9.0:
                errors.append(f"SCORING: classification '{classification}' inconsistent with score {total} (expected ~{expected})")

        return errors

    @staticmethod
    def _expected_classification(score: float) -> str:
        if score >= 9.0:
            return "Imperdível"
        elif score >= 7.5:
            return "Excelente"
        elif score >= 6.0:
            return "Bom"
        elif score >= 4.5:
            return "Aceitável"
        elif score >= 3.0:
            return "Abaixo da média"
        return "Não recomendado"


class PipelineEndToEndValidator:
    """Run all validation layers across a complete listing snapshot."""

    @classmethod
    def validate_complete(cls, raw: Dict, clean: Dict, enriched: Dict,
                          valuation: Dict, score: Dict) -> List[str]:
        errors = []
        errors.extend(ScrapingValidator.validate(raw))
        errors.extend(ETLValidator.validate(clean))
        errors.extend(CVNLPValidator.validate(enriched))
        errors.extend(ValuationValidator.validate(valuation, clean))
        errors.extend(ScoringValidator.validate(score, clean))
        return errors
