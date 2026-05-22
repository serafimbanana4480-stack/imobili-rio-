"""Scoring engine orchestrating all score calculations.

Enhanced to:
- Pass expanded data to all calculators (lat/lon, tipologia, etc.)
- Use structured red flags with penalties
- Apply red flag penalties to final score
- Guard 'Imperdível' classification against critical flags
- Include full INE market context in rationale
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import Score, CleanListing, Valuation
from realestate_engine.scoring.score_discount_calculator import ScoreDiscountCalculator
from realestate_engine.scoring.score_location_calculator import ScoreLocationCalculator
from realestate_engine.scoring.score_condition_calculator import ScoreConditionCalculator
from realestate_engine.scoring.score_liquidity_calculator import ScoreLiquidityCalculator
from realestate_engine.scoring.score_freshness_calculator import ScoreFreshnessCalculator
from realestate_engine.scoring.score_amenities_calculator import ScoreAmenitiesCalculator
from realestate_engine.scoring.red_flags_detector import RedFlagsDetector
from realestate_engine.scoring.weighted_score_calculator import WeightedScoreCalculator
from realestate_engine.scoring.rationale_generator import RationaleGenerator
from realestate_engine.monitoring.metrics import MetricsCollector
from realestate_engine.utils.decorators import async_timed

metrics = MetricsCollector()


class ScoringEngine:
    """Orchestrates scoring pipeline for all listings."""
    
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        # Use default weights with validation
        try:
            weights = self.repo.get_config("scoring_weights")
            self.weighted_calc = WeightedScoreCalculator(weights=weights if weights else None, repo=self.repo)
        except Exception as e:
            logger.warning(f"Could not load scoring_weights from config: {e}, using defaults")
            self.weighted_calc = WeightedScoreCalculator(repo=self.repo)

        self.discount_calc = ScoreDiscountCalculator()
        self.condition_calc = ScoreConditionCalculator()
        self.liquidity_calc = ScoreLiquidityCalculator()
        self.freshness_calc = ScoreFreshnessCalculator()
        self.amenities_calc = ScoreAmenitiesCalculator()
        self.red_flags = RedFlagsDetector()
        self.rationale_gen = RationaleGenerator()

    def score(self, listing: CleanListing, valuation: Optional[Valuation] = None) -> Dict:
        """Score a single listing with all factors."""

        # ── Build dicts for calculators ─────────────────────────────────
        listing_dict = {
            "preco_pedido": listing.preco_pedido,
            "area_util_m2": listing.area_util_m2,
            "quartos": listing.quartos,
            "casas_banho": listing.casas_banho,
            "freguesia": listing.freguesia,
            "concelho": listing.concelho,
            "distrito": listing.distrito,
            "estado": listing.estado,
            "ano_construcao": listing.ano_construcao,
            "cert_energetico": listing.cert_energetico,
            "tipologia": listing.tipologia,
            "preco_por_m2": listing.preco_por_m2,
            "ine_preco_medio_m2": listing.ine_preco_medio_m2,
            "ine_tendencia_mensal": listing.ine_tendencia_mensal,
            "scrape_timestamp": listing.scrape_timestamp,
            "num_fotos": listing.num_fotos,
            "source_portal": listing.source_portal,
            "titulo": listing.titulo,
            "descricao": listing.descricao,
            "lat": listing.lat,
            "lon": listing.lon,
            "dist_metro_m": listing.dist_metro_m,
            "dist_escola_m": listing.dist_escola_m,
            "dist_comercio_m": listing.dist_comercio_m,
            # NEW: CV features
            "image_quality_score": listing.image_quality_score,
            "room_detection_confidence": listing.room_detection_confidence,
            # NEW: NLP features
            "bert_sentiment_score": listing.bert_sentiment_score,
            "bert_sentiment_label": listing.bert_sentiment_label,
            # NEW: Amenities features
            "tem_garagem": listing.tem_garagem,
            "tem_piscina": listing.tem_piscina,
            "tem_vista_mar": listing.tem_vista_mar,
            "tem_vista_rio": listing.tem_vista_rio,
            "tem_elevador": listing.tem_elevador,
            "tem_terraco": listing.tem_terraco,
            "tem_jardim": listing.tem_jardim,
            "tem_ac": listing.tem_ac,
            "andar": listing.andar,
            "cozinha_separada": listing.cozinha_separada,
            "tem_maquina_lavar": listing.tem_maquina_lavar,
            "tem_maquina_louca": listing.tem_maquina_louca,
            "tem_frigorifico": listing.tem_frigorifico,
            "tem_fogao": listing.tem_fogao,
            "tem_forno": listing.tem_forno,
            "tem_estores_anti_roubo": listing.tem_estores_anti_roubo,
            "tem_monitorizacao": listing.tem_monitorizacao,
            "tem_videoporteiro": listing.tem_videoporteiro,
            "tem_internet": listing.tem_internet,
            "tem_tv_cabo": listing.tem_tv_cabo,
            "tem_telefone": listing.tem_telefone,
            "acessibilidade_mobilidade": listing.acessibilidade_mobilidade,
            "tem_aquecimento": listing.tem_aquecimento,
        }

        valuation_dict = None
        if valuation:
            valuation_dict = {
                "valor_justo": valuation.valor_justo,
                "discount": valuation.discount,
                "confianca": valuation.confianca,
                "xgboost_explanation": valuation.xgboost_explanation,
            }

        # ── Calculate individual scores ─────────────────────────────────
        discount = valuation.discount if valuation else None
        confidence = valuation.confianca if valuation else None

        scores = {
            "discount": self.discount_calc.calculate(
                discount=discount,
                confidence=confidence,
            ),
            "location": ScoreLocationCalculator.calculate(
                freguesia=listing.freguesia,
                concelho=listing.concelho,
                dist_metro=listing.dist_metro_m,
                dist_escola=listing.dist_escola_m,
                dist_comercio=listing.dist_comercio_m,
                ine_tendencia=listing.ine_tendencia_mensal,
                lat=listing.lat,
                lon=listing.lon,
            ),
            "condition": self.condition_calc.calculate(
                estado=listing.estado,
                ano_construcao=listing.ano_construcao,
                cert_energetico=listing.cert_energetico,
                image_quality_score=listing.image_quality_score,
                room_detection_confidence=listing.room_detection_confidence,
                bert_sentiment_score=listing.bert_sentiment_score,
                bert_sentiment_label=listing.bert_sentiment_label,
            ),
            "amenities": self.amenities_calc.calculate(
                tem_garagem=listing.tem_garagem,
                tem_piscina=listing.tem_piscina,
                tem_elevador=listing.tem_elevador,
                tem_ac=listing.tem_ac,
                tem_terraco=listing.tem_terraco,
                tem_jardim=listing.tem_jardim,
                cozinha_separada=listing.cozinha_separada,
                tem_maquina_lavar=listing.tem_maquina_lavar,
                tem_maquina_louca=listing.tem_maquina_louca,
                tem_frigorifico=listing.tem_frigorifico,
                tem_fogao=listing.tem_fogao,
                tem_forno=listing.tem_forno,
                tem_estores_anti_roubo=listing.tem_estores_anti_roubo,
                tem_monitorizacao=listing.tem_monitorizacao,
                tem_videoporteiro=listing.tem_videoporteiro,
                andar=listing.andar,
            ),
            "liquidity": self.liquidity_calc.calculate(
                preco_por_m2=listing.preco_por_m2,
                ine_preco_medio_m2=listing.ine_preco_medio_m2,
                area_util_m2=listing.area_util_m2,
                tipologia=listing.tipologia,
                quartos=listing.quartos,
            ),
            "freshness": self.freshness_calc.calculate(
                scrape_timestamp=listing.scrape_timestamp,
            ),
        }

        # ── Calculate weighted base score ───────────────────────────────
        base_score = self.weighted_calc.calculate(scores)

        # ── Detect red flags ────────────────────────────────────────────
        red_flag_strings = self.red_flags.detect(listing_dict, valuation_dict)
        has_critical = self.red_flags.has_critical_flags(listing_dict, valuation_dict)
        total_penalty = self.red_flags.total_penalty(listing_dict, valuation_dict)

        # Apply penalty (no cap — allow full penalties)
        penalty = total_penalty
        final_score = max(0.0, min(10.0, base_score - penalty))

        # Hard caps for missing critical data
        if listing.num_fotos == 0:
            final_score = min(final_score, 5.0)
        if listing.lat is None or listing.lon is None:
            # Missing coordinates are common in scraped listings; penalize them,
            # but don't flatten every otherwise-strong deal into the same ceiling.
            final_score = min(final_score, 7.2)
        if len(red_flag_strings) > 0:
            final_score = min(final_score, 8.0)

        # Check strict Imperdível conditions
        discount_pct = (valuation.discount * 100) if (valuation and valuation.discount) else 0.0
        has_any_flags = len(red_flag_strings) > 0
        is_truly_imperdivel = self.weighted_calc.is_imperdivel(
            final_score, discount_pct, has_any_flags
        )

        # ── Classify ────────────────────────────────────────────────────
        classificacao = self.weighted_calc.classify(final_score, is_truly_imperdivel)

        # Guard: If score is >= 9.0 but it doesn't meet the strict criteria, cap the score visually
        if final_score >= 9.0 and not is_truly_imperdivel:
            final_score = min(final_score, 8.99)

        # ── Generate rationale ──────────────────────────────────────────
        rationale = self.rationale_gen.generate(
            scores, red_flag_strings, listing_dict, valuation_dict
        )

        return {
            "score_total": round(final_score, 2),
            "score_discount": round(scores["discount"], 2),
            "score_location": round(scores["location"], 2),
            "score_condition": round(scores["condition"], 2),
            "score_amenities": round(scores["amenities"], 2),
            "score_liquidity": round(scores["liquidity"], 2),
            "score_freshness": round(scores["freshness"], 2),
            "classificacao": classificacao,
            "rationale": rationale,
            "red_flags": red_flag_strings,
            "has_critical_flags": has_critical,
            "penalty_applied": round(penalty, 2),
        }

    @async_timed
    async def score_batch(self, batch_size: int = 500) -> int:
        """Score all unscored listings that have valuations."""
        logger.info("Starting scoring batch")

        # Purity guard — warn and skip if any fake/sample records exist
        try:
            self.repo.assert_no_sample_data()
        except RuntimeError as e:
            logger.warning(f"Sample data detected — skipping affected records: {e}")

        listings = self.repo.get_clean_listings(limit=batch_size)
        if not listings:
            logger.info("No listings to score")
            return 0

        # Batch lookups eliminate N+1 query problem
        listing_ids = [l.id for l in listings]
        existing_scores = self.repo.get_scores_for_listings(listing_ids)
        valuations = self.repo.get_valuations_for_listings(listing_ids)

        scored_count = 0
        scores_to_save = []

        for listing in listings:
            # Check if already scored (batch lookup)
            if listing.id in existing_scores:
                continue

            # Get valuation (batch lookup)
            valuation = valuations.get(listing.id)
            if not valuation:
                continue

            result = self.score(listing, valuation)

            score = Score(
                listing_id=listing.id,
                score_total=result["score_total"],
                score_discount=result["score_discount"],
                score_location=result["score_location"],
                score_condition=result["score_condition"],
                score_liquidity=result["score_liquidity"],
                score_freshness=result["score_freshness"],
                classificacao=result["classificacao"],
                rationale=result["rationale"],
                red_flags=result["red_flags"],
            )
            scores_to_save.append(score)
            scored_count += 1

        if scores_to_save:
            self.repo.create_scores_batch(scores_to_save)
            logger.info(f"Scored {scored_count} listings")

            # Log classification distribution
            dist = {}
            for s in scores_to_save:
                dist[s.classificacao] = dist.get(s.classificacao, 0) + 1
            logger.info(f"Classification distribution: {dist}")

        return scored_count
