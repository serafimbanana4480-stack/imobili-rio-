"""Best opportunity selector for single best opportunity notification.

Selects the single best opportunity based on hybrid criteria:
- Composite score (score + discount + profit potential + location)
- Realism verification
- Deduplication (7-day exclusion period)
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta, UTC
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import Score, CleanListing, Valuation


class BestOpportunitySelector:
    """Selects the single best opportunity for notification."""

    def __init__(self):
        self.repo = DatabaseRepository()

    def select_single_best(self, min_score: float = 7.0) -> Optional[Dict]:
        """Select the single best opportunity for notification.

        Args:
            min_score: Minimum score threshold (default: 7.0)

        Returns:
            Dictionary with 'listing' and 'score' keys, or None if no opportunity found
        """
        logger.info(f"Selecting single best opportunity (min_score: {min_score})")

        # Get all scores above threshold
        scores = self.repo.get_top_scores(min_score=min_score, limit=5000)
        logger.info(f"Found {len(scores)} scores above threshold")

        if not scores:
            logger.info("No opportunities above threshold")
            return None

        # Filter and score each opportunity
        scored_opportunities = []
        for score in scores:
            listing = score.listing
            if not listing:
                continue

            # Check if recently notified (7-day exclusion)
            if self._check_recently_notified(listing.id):
                logger.debug(f"Skipping {listing.id}: notified in last 7 days")
                continue

            # Verify realism
            if not self._verify_realism(listing, score):
                logger.debug(f"Skipping {listing.id}: failed realism check")
                continue

            # Calculate composite score
            composite_score = self._calculate_composite_score(listing, score)

            scored_opportunities.append({
                "listing": listing,
                "score": score,
                "composite_score": composite_score,
            })

        if not scored_opportunities:
            logger.info("No opportunities after filtering")
            return None

        # Sort by composite score descending
        scored_opportunities.sort(key=lambda x: x["composite_score"], reverse=True)

        # Select the best one
        best = scored_opportunities[0]
        logger.info(
            f"Selected best opportunity: {best['listing'].id} "
            f"(score: {best['score'].score_total:.1f}, "
            f"composite: {best['composite_score']:.1f})"
        )

        return best

    def _calculate_composite_score(self, listing: CleanListing, score: Score) -> float:
        """Calculate composite score based on multiple factors.

        Composite score formula:
        - 30% current score
        - 40% discount (20% discount = 8 points)
        - 30% profit potential (normalized)
        - 10% location score

        Returns:
            Composite score (0-100)
        """
        # Base score (30% weight)
        base_score = score.score_total * 3.0  # 10/10 → 30 points

        # Discount (40% weight)
        discount_pct = 0.0
        if listing.valuations:
            discount_pct = listing.valuations[0].discount * 100 if listing.valuations[0].discount else 0.0
        discount_score = min(discount_pct * 2.0, 40.0)  # 20% discount = 40 points (max)

        # Profit potential (30% weight)
        profit_score = 0.0
        if listing.valuations and listing.valuations[0].discount:
            profit = listing.valuations[0].valor_justo - listing.preco_pedido
            # Normalize: 50k profit = 15 points, 100k profit = 30 points
            profit_score = min((profit / 50000.0) * 15.0, 30.0)

        # Location score (10% weight)
        location_score = score.score_location  # Already 0-10

        # Calculate composite
        composite = base_score + discount_score + profit_score + location_score
        return round(composite, 1)

    def _verify_realism(self, listing: CleanListing, score: Score) -> bool:
        """Verify if the opportunity is realistic.

        Checks:
        - Discount > 30% → likely error/ruin
        - Profit > 100k€ → verify valuation confidence
        - Condition score < 3.0 → penalize if not renovable
        - Critical red flags → exclude

        Returns:
            True if realistic, False otherwise
        """
        # Check discount
        if listing.valuations and listing.valuations[0].discount:
            discount_pct = listing.valuations[0].discount * 100
            if discount_pct > 30.0:
                logger.warning(f"Discount too high: {discount_pct}% for {listing.id}")
                return False

        # Check profit potential
        if listing.valuations and listing.valuations[0].discount:
            profit = listing.valuations[0].valor_justo - listing.preco_pedido
            if profit > 100000:  # > 100k€
                # Check valuation confidence
                confidence = listing.valuations[0].confianca or 0.0
                if confidence < 0.6:
                    logger.warning(f"High profit but low confidence: {profit}€ for {listing.id}")
                    return False

        # Check condition
        if score.score_condition < 3.0:
            # Allow if it's renovable (has renovation year or "por renovar" in description)
            if not (listing.ano_renovacao or
                    (listing.descricao and "renov" in listing.descricao.lower())):
                logger.warning(f"Low condition score and not renovable: {listing.id}")
                return False

        # Check critical red flags
        if score.red_flags:
            for flag in score.red_flags:
                if "🚨" in flag:  # Critical flag
                    logger.warning(f"Critical red flag: {flag} for {listing.id}")
                    return False

        return True

    def _check_recently_notified(self, listing_id: str) -> bool:
        """Check if listing was notified in the last 7 days.

        Args:
            listing_id: Listing ID to check

        Returns:
            True if notified in last 7 days, False otherwise
        """
        # Get notifications for this listing
        notifications = self.repo.get_notifications_by_listing(listing_id)

        if not notifications:
            return False

        # Check if any notification was sent in the last 7 days
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        for notif in notifications:
            if notif.created_at and notif.created_at > seven_days_ago:
                if notif.status == "sent":
                    return True

        return False
