"""Freshness score calculator (15% weight).

Fixed timezone handling and added:
- Support for both ISO format and string dates
- Price reduction detection (bonus for recently reduced prices)
- Continuous scoring curve instead of step function
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger


class ScoreFreshnessCalculator:
    """Calculates freshness score based on listing age."""

    @staticmethod
    def calculate(
        scrape_timestamp: Optional[str] = None,
        listing_date: Optional[str] = None,
        days_on_market: Optional[int] = None,
        price_recently_reduced: bool = False,
    ) -> float:
        """Calculate freshness score (0-10).

        Newer listings = higher score (first-mover advantage).
        Older listings = lower score (may have issues, less urgency).
        Price reduction on older listing = moderate bonus.
        """
        age_days = None

        # Try to compute age from dates
        if days_on_market is not None:
            age_days = days_on_market
        else:
            date = None
            for date_str in [listing_date, scrape_timestamp]:
                if not date_str:
                    continue
                try:
                    # Handle various ISO formats
                    clean = str(date_str).replace("Z", "+00:00")
                    date = datetime.fromisoformat(clean)
                    break
                except (ValueError, TypeError):
                    continue

            if date:
                now = datetime.now(timezone.utc)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - date).days)

        if age_days is None:
            return 5.0  # Unknown freshness

        # ── Continuous scoring curve ────────────────────────────────────
        if age_days <= 1:
            score = 10.0        # Published today/yesterday
        elif age_days <= 3:
            score = 9.5 - (age_days - 1) * 0.25    # 9.5 → 9.0
        elif age_days <= 7:
            score = 9.0 - (age_days - 3) * 0.375   # 9.0 → 7.5
        elif age_days <= 14:
            score = 7.5 - (age_days - 7) * 0.214   # 7.5 → 6.0
        elif age_days <= 30:
            score = 6.0 - (age_days - 14) * 0.125  # 6.0 → 4.0
        elif age_days <= 60:
            score = 4.0 - (age_days - 30) * 0.067  # 4.0 → 2.0
        elif age_days <= 90:
            score = 2.0 - (age_days - 60) * 0.033  # 2.0 → 1.0
        elif age_days <= 180:
            score = 1.0 - (age_days - 90) * 0.005  # 1.0 → 0.55
        else:
            score = 0.5

        # ── Price reduction bonus ───────────────────────────────────────
        # If the price was recently reduced on an older listing,
        # it becomes more interesting again
        if price_recently_reduced and age_days > 14:
            score = min(10.0, score + 1.5)

        return max(0.0, min(10.0, round(score, 2)))
