"""Analytics Engine for advanced real estate insights (FASE 7).

Implements:
- Zone ranking by ROI potential
- Price trend forecasting (simple linear + momentum)
- Risk scoring per zone/neighborhood
- Opportunity heatmap generation
- AI-driven alert generation
"""
from typing import Dict, List, Optional, Tuple
from statistics import mean, median, stdev
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from loguru import logger


class ZoneRankingEngine:
    """Ranks zones/freguesias by investment potential."""

    def rank_zones(self, listings: List[Dict]) -> List[Dict]:
        """Rank zones based on multiple investment criteria.

        Criteria:
        - Average discount (underpricing signal)
        - Score density (high-scoring listings per zone)
        - Price/m² vs INE benchmark
        - Infrastructure proximity (metro, schools)
        """
        zone_data = defaultdict(lambda: {
            "listings": 0,
            "avg_discount": [],
            "avg_score": [],
            "avg_price_m2": [],
            "ine_benchmark": None,
            "metro_proximity": [],
            "school_proximity": [],
        })

        for l in listings:
            zone = l.get("freguesia") or l.get("concelho") or "Unknown"
            d = zone_data[zone]
            d["listings"] += 1

            if l.get("valuation_discount") is not None:
                d["avg_discount"].append(l["valuation_discount"])
            if l.get("score_total") is not None:
                d["avg_score"].append(l["score_total"])
            if l.get("preco_por_m2") and l["preco_por_m2"] > 0:
                d["avg_price_m2"].append(l["preco_por_m2"])
            if l.get("ine_preco_medio_m2") and d["ine_benchmark"] is None:
                d["ine_benchmark"] = l["ine_preco_medio_m2"]
            if l.get("dist_metro_m") is not None:
                d["metro_proximity"].append(l["dist_metro_m"])
            if l.get("dist_escola_m") is not None:
                d["school_proximity"].append(l["dist_escola_m"])

        rankings = []
        for zone, data in zone_data.items():
            n = data["listings"]
            if n < 3:
                continue  # Need minimum sample

            # Score components (0-10 scale)
            discount_score = mean(data["avg_discount"]) * 10 if data["avg_discount"] else 0
            score_density = mean(data["avg_score"]) if data["avg_score"] else 5.0

            # Price vs INE benchmark (lower is better for buyers)
            price_m2 = median(data["avg_price_m2"]) if data["avg_price_m2"] else None
            benchmark = data["ine_benchmark"]
            price_ratio = (benchmark / price_m2) if price_m2 and benchmark and price_m2 > 0 else 1.0
            value_score = min(10, max(0, (price_ratio - 0.8) * 25))  # 0.8 ratio -> 0, 1.2 ratio -> 10

            # Infrastructure (closer = better, inverse distance)
            metro_score = 10 - min(10, mean(data["metro_proximity"]) / 200) if data["metro_proximity"] else 5.0
            school_score = 10 - min(10, mean(data["school_proximity"]) / 500) if data["school_proximity"] else 5.0

            # Composite ROI potential (weighted)
            roi_score = (
                discount_score * 0.30 +
                score_density * 0.25 +
                value_score * 0.25 +
                metro_score * 0.10 +
                school_score * 0.10
            )

            rankings.append({
                "zone": zone,
                "listings_count": n,
                "roi_score": round(roi_score, 2),
                "avg_discount_pct": round(mean(data["avg_discount"]) * 100, 1) if data["avg_discount"] else 0,
                "avg_score": round(mean(data["avg_score"]), 1) if data["avg_score"] else 0,
                "price_vs_ine": round(price_ratio, 2) if price_ratio else None,
                "metro_score": round(metro_score, 1),
                "school_score": round(school_score, 1),
            })

        rankings.sort(key=lambda x: x["roi_score"], reverse=True)
        return rankings


class PriceTrendForecaster:
    """Simple price trend forecasting based on historical data."""

    def forecast_zone_trend(self, price_history: List[Dict]) -> Dict:
        """Forecast price trend for a zone based on historical prices.

        Args:
            price_history: List of dicts with 'date' (iso) and 'price'

        Returns:
            Dict with trend direction, momentum, and forecast
        """
        if len(price_history) < 3:
            return {"direction": "insufficient_data", "confidence": 0.0}

        # Sort by date
        sorted_hist = sorted(price_history, key=lambda x: x.get("date", ""))
        prices = [h["price"] for h in sorted_hist if h.get("price")]

        if len(prices) < 3:
            return {"direction": "insufficient_data", "confidence": 0.0}

        # Simple linear regression slope
        n = len(prices)
        x_mean = (n - 1) / 2
        y_mean = mean(prices)
        numerator = sum((i - x_mean) * (p - y_mean) for i, p in enumerate(prices))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator else 0

        # Volatility (coefficient of variation)
        if y_mean > 0:
            cv = (stdev(prices) / y_mean) if len(prices) > 1 else 0
        else:
            cv = 0

        # Momentum: last 3 vs previous 3
        recent = mean(prices[-3:]) if len(prices) >= 3 else mean(prices)
        previous = mean(prices[-6:-3]) if len(prices) >= 6 else mean(prices[:max(1, n // 2)])
        momentum = ((recent - previous) / previous) * 100 if previous else 0

        # Direction
        if slope > y_mean * 0.005:  # >0.5% growth per period
            direction = "rising"
        elif slope < -y_mean * 0.005:
            direction = "falling"
        else:
            direction = "stable"

        # Confidence based on data volume and volatility
        confidence = min(1.0, max(0.3, (n / 20) * (1 - cv)))

        # 30-day forecast (assuming monthly data points)
        forecast_price = prices[-1] + slope * 1 if prices else None

        return {
            "direction": direction,
            "momentum_pct": round(momentum, 2),
            "slope": round(slope, 2),
            "volatility_cv": round(cv, 3),
            "confidence": round(confidence, 2),
            "forecast_30d": round(forecast_price, 2) if forecast_price else None,
            "data_points": n,
        }


class RiskAnalyzer:
    """Analyzes risk factors for real estate investments per zone."""

    RISK_FACTORS = {
        "price_volatility": 0.25,
        "low_liquidity": 0.20,
        "high_overpricing": 0.20,
        "infrastructure_gap": 0.15,
        "market_saturation": 0.20,
    }

    def analyze_zone_risk(self, listings: List[Dict]) -> Dict:
        """Calculate risk score for a zone (0 = low risk, 10 = high risk)."""
        if not listings:
            return {"risk_score": None, "factors": {}}

        prices = [l["preco_pedido"] for l in listings if l.get("preco_pedido")]
        scores = [l["score_total"] for l in listings if l.get("score_total") is not None]
        discounts = [l.get("valuation_discount", 0) for l in listings if l.get("valuation_discount") is not None]
        metro_dists = [l["dist_metro_m"] for l in listings if l.get("dist_metro_m") is not None]

        factors = {}

        # Price volatility
        if len(prices) > 1 and mean(prices) > 0:
            cv = stdev(prices) / mean(prices)
            factors["price_volatility"] = min(10, cv * 20)  # Scale CV to 0-10
        else:
            factors["price_volatility"] = 5.0

        # Liquidity (inverse of score density — lower scores = harder to sell)
        if scores:
            liquidity = 10 - mean(scores)
            factors["low_liquidity"] = max(0, liquidity)
        else:
            factors["low_liquidity"] = 5.0

        # Overpricing (negative discount = overpriced)
        if discounts:
            overpriced_ratio = sum(1 for d in discounts if d < 0) / len(discounts)
            factors["high_overpricing"] = overpriced_ratio * 10
        else:
            factors["high_overpricing"] = 5.0

        # Infrastructure gap
        if metro_dists:
            avg_metro = mean(metro_dists)
            factors["infrastructure_gap"] = min(10, avg_metro / 300)
        else:
            factors["infrastructure_gap"] = 5.0

        # Market saturation (too many listings = saturated)
        n = len(listings)
        factors["market_saturation"] = min(10, n / 50)  # 50+ listings = saturated

        # Weighted composite
        risk_score = sum(factors[k] * self.RISK_FACTORS[k] for k in factors)

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": "low" if risk_score < 3 else "medium" if risk_score < 6 else "high",
            "factors": {k: round(v, 2) for k, v in factors.items()},
            "listing_count": n,
        }


class AlertGenerator:
    """AI-driven alert generation for investment opportunities."""

    def generate_alerts(self, new_listings: List[Dict], historical_context: List[Dict]) -> List[Dict]:
        """Generate prioritized alerts for new listings.

        Alert types:
        - PRICE_DROP: Price significantly below historical average for zone
        - HIGH_SCORE: Score >= 8.5 with strong fundamentals
        - RARE_TYPE: Unusual typology in zone (e.g., T4 in T2-dominated area)
        - FAST_MARKET: Listing in high-liquidity zone with good discount
        """
        alerts = []

        # Build zone historical context
        zone_prices = defaultdict(list)
        zone_typologies = defaultdict(lambda: defaultdict(int))
        for h in historical_context:
            zone = h.get("freguesia") or "Unknown"
            if h.get("preco_por_m2"):
                zone_prices[zone].append(h["preco_por_m2"])
            if h.get("tipologia"):
                zone_typologies[zone][h["tipologia"]] += 1

        for listing in new_listings:
            zone = listing.get("freguesia") or "Unknown"
            price_m2 = listing.get("preco_por_m2")
            score = listing.get("score_total")
            discount = listing.get("valuation_discount")
            tipology = listing.get("tipologia")

            # Alert: Price drop
            if zone_prices[zone] and price_m2:
                zone_median = median(zone_prices[zone])
                if zone_median > 0 and price_m2 < zone_median * 0.85:
                    alerts.append({
                        "type": "PRICE_DROP",
                        "priority": "high" if price_m2 < zone_median * 0.75 else "medium",
                        "listing_id": listing.get("source_id"),
                        "message": f"Preço/m² {price_m2:.0f}€ 15%+ abaixo da mediana da zona ({zone_median:.0f}€)",
                        "zone": zone,
                        "score_boost": 1.5,
                    })

            # Alert: High score
            if score and score >= 8.5:
                alerts.append({
                    "type": "HIGH_SCORE",
                    "priority": "high",
                    "listing_id": listing.get("source_id"),
                    "message": f"Score {score:.1f}/10 — oportunidade excepcional",
                    "zone": zone,
                    "score_boost": 1.0,
                })

            # Alert: Rare typology
            if tipology and zone_typologies[zone]:
                total = sum(zone_typologies[zone].values())
                type_count = zone_typologies[zone].get(tipology, 0)
                if total > 10 and type_count / total < 0.05:
                    alerts.append({
                        "type": "RARE_TYPE",
                        "priority": "medium",
                        "listing_id": listing.get("source_id"),
                        "message": f"{tipology} raro em {zone} (apenas {type_count}/{total} listagens)",
                        "zone": zone,
                        "score_boost": 0.5,
                    })

        # Sort by priority and score boost
        priority_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda a: (priority_order.get(a["priority"], 99), -a.get("score_boost", 0)))
        return alerts
