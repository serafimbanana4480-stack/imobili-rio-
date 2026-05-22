"""Condition score calculator (15% weight).

Enhanced with:
- More granular state mapping
- Renovation recency bonus
- Energy certificate impact curves
- Age-based depreciation model
- Combined assessment logic
"""
from typing import Optional
from datetime import datetime
from loguru import logger


class ScoreConditionCalculator:
    """Calculates condition score based on state, year built, and energy cert."""

    # ── State scores ────────────────────────────────────────────────────
    ESTADO_SCORES = {
        "novo": 9.5,
        "em_construcao": 9.0,
        "renovado": 8.5,
        "remodelado": 8.5,
        "como novo": 8.0,
        "bom": 6.5,
        "razoavel": 5.0,
        "usado": 4.5,
        "aceitavel": 4.5,
        "para_recuperar": 2.5,
        "para recuperar": 2.5,
        "ruina": 1.0,
        # English aliases
        "new": 9.5,
        "renovated": 8.5,
        "remodeled": 8.5,
        "good": 6.5,
        "acceptable": 4.5,
        "ruin": 1.0,
    }

    # ── Energy certificate impact ───────────────────────────────────────
    CERT_ADJUSTMENTS = {
        "A+": 1.5, "A": 1.2, "A-": 0.8,
        "B": 0.5, "B-": 0.3,
        "C": 0.0,
        "D": -0.3,
        "E": -0.7,
        "F": -1.2,
        "G": -1.5,
    }

    @classmethod
    def calculate(
        cls,
        estado: Optional[str] = None,
        ano_construcao: Optional[int] = None,
        cert_energetico: Optional[str] = None,
        ano_renovacao: Optional[int] = None,
        image_quality_score: Optional[float] = None,
        room_detection_confidence: Optional[float] = None,
        bert_sentiment_score: Optional[float] = None,
        bert_sentiment_label: Optional[str] = None,
    ) -> float:
        """Calculate condition score (0-10)."""
        score = 5.0  # Default: unknown condition

        # ── 1. Conservation state (primary factor) ──────────────────────
        if estado:
            estado_lower = estado.lower().strip()
            for key, val in cls.ESTADO_SCORES.items():
                if key in estado_lower or estado_lower in key:
                    score = val
                    break

        # ── 2. Age adjustment ───────────────────────────────────────────
        current_year = datetime.now().year
        if ano_construcao and ano_construcao > 1800:
            age = current_year - ano_construcao

            # Renovation overrides age penalty
            effective_age = age
            if ano_renovacao and ano_renovacao > ano_construcao:
                effective_age = current_year - ano_renovacao

            if effective_age < 2:
                score = max(score, 9.0)  # Essentially new
                score += 0.5
            elif effective_age < 5:
                score += 0.8
            elif effective_age < 10:
                score += 0.3
            elif effective_age < 20:
                pass  # No adjustment
            elif effective_age < 30:
                score -= 0.3
            elif effective_age < 50:
                score -= 0.8
            elif effective_age < 80:
                score -= 1.2
            else:
                score -= 1.8  # Very old

        # ── 3. Energy certificate adjustment ────────────────────────────
        if cert_energetico:
            cert = cert_energetico.upper().strip()
            adj = cls.CERT_ADJUSTMENTS.get(cert, 0.0)
            score += adj

        # ── 4. Image quality adjustment (NEW) ───────────────────────────
        if image_quality_score is not None:
            if image_quality_score < 0.3:
                score -= 1.0  # Poor quality images
            elif image_quality_score > 0.8:
                score += 0.5  # High quality images

        # ── 5. Room detection confidence adjustment (NEW) ───────────────
        if room_detection_confidence is not None:
            if room_detection_confidence < 0.5:
                score -= 0.5  # Unclear room layout
            elif room_detection_confidence > 0.8:
                score += 0.3  # Clear room layout

        # ── 6. BERT sentiment adjustment (NEW) ───────────────────────────
        if bert_sentiment_score is not None:
            # Higher sentiment generally correlates with better listing quality.
            if bert_sentiment_score > 0.4:
                score += 0.3
            elif bert_sentiment_score < -0.4:
                score -= 0.4

        if bert_sentiment_label:
            sentiment_label = bert_sentiment_label.upper().strip()
            if sentiment_label == "POSITIVE":
                score += 0.1
            elif sentiment_label == "NEGATIVE":
                score -= 0.1

        return max(0.0, min(10.0, round(score, 2)))
