"""Opportunity selector for notifications."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.utils.config import config


class OpportunitySelector:
    """Selects top opportunities for notification."""
    
    def __init__(self):
        self.repo = DatabaseRepository()
    
    def select(
        self,
        min_score: float = None,
        max_notifications: int = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        freguesias: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Select top opportunities for notification."""
        min_score = min_score or config.min_score_notification
        max_notifications = max_notifications or config.max_daily_notifications
        
        # Get today's notification count
        sent_today = self.repo.get_notifications_sent_today()
        remaining = max(0, max_notifications - sent_today)
        
        if remaining <= 0:
            logger.info("Daily notification limit reached")
            return []
        
        # Get top scores
        scores = self.repo.get_top_scores(min_score=min_score, limit=remaining * 2)
        
        # Convert to dicts and filter
        opportunities = []
        for score in scores:
            listing = score.listing
            if not listing:
                continue
            
            # Price filters
            if price_min and listing.preco_pedido < price_min:
                continue
            if price_max and listing.preco_pedido > price_max:
                continue
            
            # Freguesia filter
            if freguesias:
                listing_freg = (listing.freguesia or "").lower().strip()
                if not any(f.lower().strip() in listing_freg for f in freguesias):
                    continue
            
            # Check if already notified
            existing = self.repo.get_notifications_sent_today()  # Simplified
            
            opportunities.append({
                "listing": listing,
                "score": score,
            })
        
        # Sort by score total descending, then by discount
        opportunities.sort(key=lambda x: (
            -x["score"].score_total,
            -(x["score"].listing.valuations[0].discount if x["score"].listing.valuations else 0)
        ))
        
        selected = opportunities[:remaining]
        logger.info(f"Selected {len(selected)} opportunities for notification")
        return selected
