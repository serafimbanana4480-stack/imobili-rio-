"""
Advanced NLP module for Real Estate Engine
"""

from .bert_portuguese import BERTPortugueseProcessor
from .sentiment_analyzer import SentimentAnalyzer
from .ner_extractor import NERExtractor
from .summarizer import DescriptionSummarizer

__all__ = [
    'BERTPortugueseProcessor',
    'SentimentAnalyzer',
    'NERExtractor',
    'DescriptionSummarizer'
]
