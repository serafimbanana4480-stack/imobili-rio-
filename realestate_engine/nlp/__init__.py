"""
Advanced NLP module for Real Estate Engine.
All Portuguese NLP is consolidated under nlp.portuguese.
"""

from .portuguese.bert_portuguese import BERTPortugueseProcessor
from .portuguese.sentiment_analyzer import SentimentAnalyzer
from .portuguese.ner_extractor import NERExtractor
from .portuguese.summarizer import DescriptionSummarizer
from .portuguese.analyzer import (
    PortugueseNLPProcessor,
    ExtractedEntity,
    get_nlp_processor,
    analyze_portuguese_description,
)

__all__ = [
    'BERTPortugueseProcessor',
    'SentimentAnalyzer',
    'NERExtractor',
    'DescriptionSummarizer',
    'PortugueseNLPProcessor',
    'ExtractedEntity',
    'get_nlp_processor',
    'analyze_portuguese_description',
]
