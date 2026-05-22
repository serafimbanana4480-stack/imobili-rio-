"""Discount score calculator (30% weight).

Uses a smooth sigmoid-like curve for more nuanced scoring:
- Penalties for overpriced properties
- Gradual scaling through normal discount range
- Bonus zone for deep discounts
- Confidence adjustment from valuation quality
"""
from typing import Optional
from loguru import logger


class ScoreDiscountCalculator:
    """Calculates discount score based on difference between asking price and fair value."""

    @staticmethod
    def calculate(discount: Optional[float], confidence: Optional[float] = None) -> float:
        """Calculate discount score (0-10).

        Smooth curve:
          ≤ -20% (overpriced 20%+)  → 0.0
          -10%   (overpriced 10%)   → 1.5
           0%    (at market value)  → 3.0
           5%    discount           → 4.5
          10%    discount           → 6.0
          15%    discount           → 7.5
          20%    discount           → 8.5
          25%    discount           → 9.3
          30%+   discount           → 10.0
        """
        if discount is None:
            return 5.0  # No valuation data = neutral

        # Convert to percentage points for easier math
        d = discount * 100  # e.g., 0.20 → 20

        if d >= 30:
            score = 10.0
        elif d >= 25:
            score = 9.3 + (d - 25) / 5 * 0.7       # 9.3 → 10.0
        elif d >= 20:
            score = 8.5 + (d - 20) / 5 * 0.8       # 8.5 → 9.3
        elif d >= 15:
            score = 7.5 + (d - 15) / 5 * 1.0       # 7.5 → 8.5
        elif d >= 10:
            score = 6.0 + (d - 10) / 5 * 1.5       # 6.0 → 7.5
        elif d >= 5:
            score = 4.5 + (d - 5) / 5 * 1.5        # 4.5 → 6.0
        elif d >= 0:
            score = 3.0 + d / 5 * 1.5              # 3.0 → 4.5
        elif d >= -10:
            score = 1.5 + (d + 10) / 10 * 1.5      # 1.5 → 3.0
        elif d >= -20:
            score = 0.0 + (d + 20) / 10 * 1.5      # 0.0 → 1.5
        else:
            score = 0.0  # Extremely overpriced

        # Confidence adjustment: reduce score if valuation is uncertain
        if confidence is not None and confidence < 0.5:
            # Dampen extreme scores when confidence is low
            score = score * 0.7 + 5.0 * 0.3  # Pull towards neutral

        return max(0.0, min(10.0, round(score, 2)))
