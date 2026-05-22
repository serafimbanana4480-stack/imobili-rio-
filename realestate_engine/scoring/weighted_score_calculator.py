"""Weighted score calculator combining all factors.

Enhanced with:
- Configurable weights (instance-level override)
- More granular classification (6 tiers instead of 5)
- Imperdível threshold requires extreme rigor (e.g. >20% discount, zero red flags)
- Weight validation to prevent score manipulation
- Audit trail for weight changes
"""
from __future__ import annotations

import math
import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from loguru import logger

from realestate_engine.database.repository import DatabaseRepository

UTC = timezone.utc


class WeightValidationError(Exception):
    """Raised when weights are invalid."""
    pass


@dataclass
class WeightConfig:
    """Validated weight configuration."""
    weights: Dict[str, float]
    validated_at: datetime
    validated_by: str
    checksum: str

    def calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification."""
        weights_str = json.dumps(self.weights, sort_keys=True)
        return hashlib.sha256(weights_str.encode()).hexdigest()


class WeightedScoreCalculator:
    """Weighted score calculator with validation and audit trail."""

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

    MIN_WEIGHT = 0.0
    MAX_WEIGHT = 1.0
    MAX_SINGLE_WEIGHT = 0.6  # No single factor can exceed 60%
    SUM_TOLERANCE = 0.05  # Allow 5% deviation from 1.0

    def __init__(self, weights: Optional[Dict[str, float]] = None, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        if weights:
            self.weights = self._validate_weights(weights)
        else:
            self.weights = self.DEFAULT_WEIGHTS.copy()

        self.current_config = WeightConfig(
            weights=self.weights,
            validated_at=datetime.now(timezone.utc),
            validated_by="system",
            checksum=self._calculate_checksum()
        )

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Validate weight configuration."""
        # Check 1: All weights in valid range
        for key, value in weights.items():
            if not isinstance(value, (int, float)):
                raise WeightValidationError(
                    f"Weight {key} must be numeric, got {type(value)}"
                )
            if value < self.MIN_WEIGHT or value > self.MAX_WEIGHT:
                raise WeightValidationError(
                    f"Weight {key} must be in [{self.MIN_WEIGHT}, {self.MAX_WEIGHT}], got {value}"
                )

        # Check 2: All required weights present
        required_keys = set(self.DEFAULT_WEIGHTS.keys())
        provided_keys = set(weights.keys())
        missing_keys = required_keys - provided_keys
        if missing_keys:
            raise WeightValidationError(
                f"Missing required weights: {missing_keys}"
            )

        # Check 3: No extra weights
        extra_keys = provided_keys - required_keys
        if extra_keys:
            raise WeightValidationError(
                f"Unexpected weights provided: {extra_keys}"
            )

        # Check 4: Weights sum to 1.0 (with tolerance)
        total = sum(weights.values())
        if not math.isclose(total, 1.0, rel_tol=self.SUM_TOLERANCE):
            raise WeightValidationError(
                f"Weights must sum to 1.0 (±{self.SUM_TOLERANCE}), got {total:.4f}"
            )

        # Check 5: No single weight dominates
        max_weight = max(weights.values())
        if max_weight > self.MAX_SINGLE_WEIGHT:
            raise WeightValidationError(
                f"No single weight can exceed {self.MAX_SINGLE_WEIGHT}, got {max_weight:.4f}"
            )

        logger.info(f"Weights validated successfully: {weights}")

        return weights

    def _calculate_checksum(self) -> str:
        """Calculate checksum for current weights."""
        weights_str = json.dumps(self.weights, sort_keys=True)
        return hashlib.sha256(weights_str.encode()).hexdigest()

    def update_weights(
        self,
        new_weights: Dict[str, float],
        changed_by: str = "system",
        reason: str = "Weight update"
    ) -> None:
        """Update weights with validation and audit trail."""
        # Validate new weights
        validated_weights = self._validate_weights(new_weights)

        # Calculate checksum
        checksum = self._calculate_checksum()

        # Log change to audit trail
        try:
            self.repo.create_weight_change_audit(
                old_weights=self.weights,
                new_weights=validated_weights,
                changed_by=changed_by,
                reason=reason,
                checksum=checksum
            )
            logger.info(
                f"Weight change audit: changed_by={changed_by}, reason={reason}"
            )
        except Exception as e:
            logger.warning(f"Failed to log weight change audit: {e}")

        # Update weights
        old_weights = self.weights.copy()
        self.weights = validated_weights
        self.current_config = WeightConfig(
            weights=self.weights,
            validated_at=datetime.now(timezone.utc),
            validated_by=changed_by,
            checksum=checksum
        )

        logger.info(f"Weights updated successfully. Diff: {checksum}")

    def get_current_config(self) -> WeightConfig:
        """Get current weight configuration."""
        return self.current_config

    # Classification thresholds
    CLASSIFICATIONS = [
        (9.0,  "Imperdível",       "🔥"),
        (7.5,  "Excelente",        "⭐"),
        (6.0,  "Bom",              "✅"),
        (4.5,  "Aceitável",        "➡️"),
        (3.0,  "Abaixo da média",  "⬇️"),
        (0.0,  "Não recomendado",  "❌"),
    ]

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
        - Overall Score >= 9.0
        - Absolute minimum discount of 15% vs market value
        - ZERO red flags (not even minor warnings)
        """
        return (
            score >= 9.0 and
            discount_pct >= 15.0 and
            not has_any_flags
        )

