"""
Enhanced Feature Engineering Module

Provides advanced feature extraction for real estate valuation including:
- Micro-location features (<100m precision)
- NLP features for Portuguese text analysis
- Market dynamics features
- Economic indicators
- Seasonal adjustments
"""

from .micro_location import (
    MicroLocationEngine,
    get_micro_location_engine,
    extract_micro_location_features,
)
from .nlp_portuguese import (
    PortugueseNLPProcessor,
    get_nlp_processor,
    analyze_portuguese_description,
)

__all__ = [
    "MicroLocationEngine",
    "get_micro_location_engine", 
    "extract_micro_location_features",
    "PortugueseNLPProcessor",
    "get_nlp_processor",
    "analyze_portuguese_description",
]
