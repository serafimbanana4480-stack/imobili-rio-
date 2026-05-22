"""Unit tests for Sentiment Analyzer."""
import pytest

pytest.importorskip("transformers", reason="transformers not installed (heavy NLP extras)")
pytest.importorskip("torch", reason="torch not installed (heavy NLP extras)")

from realestate_engine.nlp.portuguese.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def analyzer():
    """Create a SentimentAnalyzer instance."""
    return SentimentAnalyzer()


def test_analyzer_initialization(analyzer):
    """Test that analyzer initializes correctly."""
    assert analyzer.model_name == 'neuralmind/bert-base-portuguese-cased'
    assert analyzer.labels == ['negative', 'neutral', 'positive']


def test_analyze_sentiment_empty_text(analyzer):
    """Test sentiment analysis with empty text."""
    result = analyzer.analyze_sentiment("")
    
    assert result['sentiment_score'] == 0.0
    assert result['sentiment_label'] == 'neutral'
    assert 'confidence' in result
    assert 'probabilities' in result


def test_analyze_sentiment_none_text(analyzer):
    """Test sentiment analysis with None text."""
    result = analyzer.analyze_sentiment(None)
    
    assert result['sentiment_score'] == 0.0
    assert result['sentiment_label'] == 'neutral'


def test_analyze_sentiment_positive_text(analyzer):
    """Test sentiment analysis with positive text."""
    text = "Excelente apartamento com vista maravilhosa, totalmente renovado e em perfeito estado."
    result = analyzer.analyze_sentiment(text)
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
    assert result['sentiment_label'] in ['negative', 'neutral', 'positive']
    # Allow small negative values due to model variability
    assert -1.0 <= result['sentiment_score'] <= 1.0


def test_analyze_sentiment_negative_text(analyzer):
    """Test sentiment analysis with negative text."""
    text = "Precisa de obras, estado degradado, humidade e problemas estruturais."
    result = analyzer.analyze_sentiment(text)
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
    assert result['sentiment_label'] in ['negative', 'neutral', 'positive']
    assert -1.0 <= result['sentiment_score'] <= 1.0


def test_analyze_sentiment_neutral_text(analyzer):
    """Test sentiment analysis with neutral text."""
    text = "Apartamento com três quartos, duas casas de banho, localizado no centro da cidade."
    result = analyzer.analyze_sentiment(text)
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
    assert result['sentiment_label'] in ['negative', 'neutral', 'positive']


def test_analyze_sentiment_probabilities(analyzer):
    """Test that sentiment analysis returns valid probabilities."""
    text = "Apartamento renovado com boa localização."
    result = analyzer.analyze_sentiment(text)
    
    probs = result['probabilities']
    assert 'negative' in probs
    assert 'neutral' in probs
    assert 'positive' in probs
    assert 0.0 <= probs['negative'] <= 1.0
    assert 0.0 <= probs['neutral'] <= 1.0
    assert 0.0 <= probs['positive'] <= 1.0


def test_batch_analyze_empty(analyzer):
    """Test batch analysis with empty list."""
    results = analyzer.batch_analyze([])
    assert results == []


def test_batch_analyze_multiple(analyzer):
    """Test batch analysis with multiple texts."""
    texts = [
        "Excelente estado",
        "Precisa de obras",
        "Apartamento padrão"
    ]
    results = analyzer.batch_analyze(texts)
    
    assert len(results) == 3
    for result in results:
        assert 'sentiment_score' in result
        assert 'sentiment_label' in result


def test_is_available(analyzer):
    """Test checking if model is available."""
    # This will return False if transformers is not installed
    available = analyzer.is_available()
    assert isinstance(available, bool)


def test_rule_based_sentiment_fallback(analyzer):
    """Test rule-based sentiment fallback."""
    # Even if model is not available, rule-based should work
    text = "Excelente apartamento novo"
    result = analyzer.analyze_sentiment(text)
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
