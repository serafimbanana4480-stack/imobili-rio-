"""Unit tests for ScoreFreshnessCalculator."""
import pytest
from realestate_engine.scoring.score_freshness_calculator import ScoreFreshnessCalculator


class TestScoreFreshnessCalculator:
    """Test freshness score calculator."""

    def test_calculate_very_fresh(self):
        calc = ScoreFreshnessCalculator()
        from datetime import datetime, timezone, timedelta
        recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        score = calc.calculate(scrape_timestamp=recent_date)
        assert score > 8  # Very fresh listing should score high

    def test_calculate_old(self):
        calc = ScoreFreshnessCalculator()
        from datetime import datetime, timezone, timedelta
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        score = calc.calculate(scrape_timestamp=old_date)
        assert score < 5  # Old listing should score lower

    def test_calculate_missing_timestamp(self):
        calc = ScoreFreshnessCalculator()
        score = calc.calculate(scrape_timestamp=None)
        assert 0 <= score <= 10

    def test_calculate_days_on_market(self):
        calc = ScoreFreshnessCalculator()
        score = calc.calculate(days_on_market=5)
        assert score > 7  # 5 days on market should score high

    def test_calculate_price_reduction_bonus(self):
        calc = ScoreFreshnessCalculator()
        from datetime import datetime, timezone, timedelta
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        score = calc.calculate(scrape_timestamp=old_date, price_recently_reduced=True)
        assert score > 5  # Price reduction should give bonus even for older listing

    def test_calculate_recent_few_days(self):
        calc = ScoreFreshnessCalculator()
        score = calc.calculate(days_on_market=2)
        assert 0 <= score <= 10
