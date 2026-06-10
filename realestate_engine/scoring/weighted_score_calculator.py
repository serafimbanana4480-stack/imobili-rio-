"""Weighted score calculator combining all factors.

Enhanced with:
- Configurable weights (instance-level override)
- More granular classification (6 tiers instead of 5)
- Imperdível threshold requires extreme rigor (e.g. >20% discount, zero red flags)
"""
from typing import Dict, List, Optional
from loguru import logger

from realestate_engine.utils.config import config


class WeightedScoreCalculator:
    """Calculates final weighted score from individual factor scores."""

    # Default weights aligned with the Enterprise Master Plan (sum = 1.0)
    # ADJUSTED: Reduced discount weight from 0.45 to 0.20 to prevent over-reliance on discount
    # Added amenities component (0.15) to reward structural features
    DEFAULT_WEIGHTS = {
        "discount": 0.20,      # Reduced from 0.45: is it a massive bargain?
        "location": 0.25,      # Increased from 0.20: where is it?
        "condition": 0.15,     # Same: what state is it in?
        "amenities": 0.15,     # NEW: structural features (garage, AC, equipment, etc.)
        "liquidity": 0.15,     # Increased from 0.10: can I resell it?
        "freshness": 0.10,     # Same: how fresh is the listing?
    }

    # Classification thresholds
    CLASSIFICATIONS = [
        (9.0,  "Imperdível",       "🔥"),
        (7.5,  "Excelente",        "⭐"),
        (6.0,  "Bom",              "✅"),
        (4.5,  "Aceitável",        "➡️"),
        (3.0,  "Abaixo da média",  "⬇️"),
        (0.0,  "Não recomendado",  "❌"),
    ]

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate(self, scores: Dict[str, float]) -> float:
        """Calculate weighted total score (0-10)."""
        total = 0.0
        total_weight = 0.0

        for factor, weight in self.weights.items():
            score = scores.get(factor, 5.0)  # Default neutral if missing
            total += score * weight
            total_weight += weight

        # Normalize if weights don't sum to 1
        if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
            total = total / total_weight

        return round(max(0.0, min(10.0, total)), 2)

    @classmethod
    def classify(cls, score: float, is_imperdivel_verified: bool = False) -> str:
        """Classify score into human-readable category."""
        if score >= 9.0 and not is_imperdivel_verified:
            # Downgrade to Excelente if score is >= 9.0 but it doesn't pass the rigorous check
            return "Excelente"
        
        for threshold, label, _ in cls.CLASSIFICATIONS:
            if score >= threshold:
                return label
        return "Não recomendado"

    @classmethod
    def classify_with_emoji(cls, score: float, is_imperdivel_verified: bool = False) -> tuple:
        """Classify score and return (label, emoji) tuple."""
        if score >= 9.0 and not is_imperdivel_verified:
            return "Excelente", "⭐"

        for threshold, label, emoji in cls.CLASSIFICATIONS:
            if score >= threshold:
                return label, emoji
        return "Não recomendado", "❌"

    @classmethod
    def is_imperdivel(cls, score: float, discount_pct: float, has_any_flags: bool = False) -> bool:
        """Check if score qualifies as 'Imperdível'.

        Ultra-strict requirements for money-making deals:
        - Overall Score >= config.imperdivel_min_score
        - Absolute minimum discount of config.imperdivel_min_discount_pct% vs market value
        - ZERO red flags (not even minor warnings)
        """
        return (
            score >= config.imperdivel_min_score and
            discount_pct >= config.imperdivel_min_discount_pct and
            not has_any_flags
        )
