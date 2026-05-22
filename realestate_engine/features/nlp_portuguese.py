"""
Backward-compatibility shim for Portuguese NLP features.

The canonical location is now: realestate_engine.nlp.portuguese.analyzer
"""

from realestate_engine.nlp.portuguese.analyzer import (
    PortugueseNLPProcessor,
    ExtractedEntity,
    get_nlp_processor,
    analyze_portuguese_description,
)

__all__ = [
    "PortugueseNLPProcessor",
    "ExtractedEntity",
    "get_nlp_processor",
    "analyze_portuguese_description",
]
