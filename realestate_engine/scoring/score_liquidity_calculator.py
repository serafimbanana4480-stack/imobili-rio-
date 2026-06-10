"""Liquidity score calculator (15% weight).

Assesses how easily a property can be resold based on:
- Price/m² relative to market median
- Property size (T1-T2 most liquid in Porto)
- Typology demand
- Market activity (transaction volume)
"""
from typing import Optional
from loguru import logger


class ScoreLiquidityCalculator:
    """Calculates liquidity score based on price, size, and market conditions."""

    @staticmethod
    def calculate(
        preco_por_m2: Optional[float] = None,
        ine_preco_medio_m2: Optional[float] = None,
        area_util_m2: Optional[float] = None,
        tipologia: Optional[str] = None,
        quartos: Optional[int] = None,
    ) -> float:
        """Calculate liquidity score (0-10).

        Higher score = easier to sell / more market demand.
        """
        score = 5.0
        adjustments = 0

        # ── 1. Price relative to market (most important) ────────────────
        if preco_por_m2 and ine_preco_medio_m2 and ine_preco_medio_m2 > 0:
            ratio = preco_por_m2 / ine_preco_medio_m2
            adjustments += 1

            if ratio < 0.70:
                score += 2.5    # Way below market = very liquid
            elif ratio < 0.85:
                score += 1.5    # Below market
            elif ratio < 1.0:
                score += 0.5    # Slightly below
            elif ratio < 1.10:
                pass            # At market
            elif ratio < 1.25:
                score -= 0.5    # Above market
            elif ratio < 1.50:
                score -= 1.5    # Well above
            else:
                score -= 2.5    # Hard to sell at this price

        # ── 2. Size factor (sweet spot: 50-90m² in Porto) ───────────────
        if area_util_m2:
            adjustments += 1

            if 50 <= area_util_m2 <= 90:
                score += 1.0    # Sweet spot — highest demand
            elif 35 <= area_util_m2 < 50:
                score += 0.5    # Studios/T1 — good demand
            elif 90 < area_util_m2 <= 130:
                score += 0.3    # Family size — decent demand
            elif 130 < area_util_m2 <= 180:
                score -= 0.5    # Large — smaller buyer pool
            elif area_util_m2 > 180:
                score -= 1.5    # Very large — niche market
            elif area_util_m2 < 35:
                score -= 0.3    # Micro — limited appeal

        # ── 3. Typology demand (Porto market 2025-2026) ─────────────────
        rooms = quartos or 0
        if tipologia:
            tipologia_upper = tipologia.upper().strip()
            adjustments += 1

            if tipologia_upper in ("T1", "T2") or rooms in (1, 2):
                score += 1.0    # Highest demand in Porto
            elif tipologia_upper == "T3" or rooms == 3:
                score += 0.5    # Strong family demand
            elif tipologia_upper == "T0" or rooms == 0:
                score += 0.3    # Student/rental demand
            elif tipologia_upper in ("T4", "T5") or rooms >= 4:
                score -= 0.5    # Niche — smaller pool
        elif rooms:
            adjustments += 1
            if rooms in (1, 2):
                score += 1.0
            elif rooms == 3:
                score += 0.5
            elif rooms >= 4:
                score -= 0.5

        return max(0.0, min(10.0, round(score, 2)))
