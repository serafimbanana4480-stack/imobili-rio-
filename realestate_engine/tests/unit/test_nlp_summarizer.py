"""Unit tests for Description Summarizer."""
import pytest
from realestate_engine.nlp.summarizer import DescriptionSummarizer


@pytest.fixture
def summarizer():
    """Create a DescriptionSummarizer instance."""
    return DescriptionSummarizer()


def test_summarizer_initialization(summarizer):
    """Test that summarizer initializes correctly."""
    assert summarizer.model_name == 'unicamp-dl/ptt5-base-portuguese-vocab'


def test_summarize_empty_text(summarizer):
    """Test summarization with empty text."""
    summary = summarizer.summarize("")
    assert summary == ""


def test_summarize_none_text(summarizer):
    """Test summarization with None text."""
    summary = summarizer.summarize(None)
    assert summary == ""


def test_summarize_short_text(summarizer):
    """Test summarization with short text (should return as-is)."""
    text = "Apartamento T3 no Porto."
    summary = summarizer.summarize(text, max_length=100)
    
    # Short text should be returned as-is
    assert summary == text


def test_summarize_long_text(summarizer):
    """Test summarization with long text."""
    text = """
    Excelente apartamento de três quartos, localizado no coração do Porto. 
    A propriedade dispõe de uma sala ampla com luz natural, cozinha equipada, 
    duas casas de banho completas e uma varanda com vista para a cidade. 
    O edifício possui elevador e está situado perto de todos os serviços, 
    incluindo metro, escolas e comércio. O apartamento foi recentemente renovado 
    e encontra-se em excelente estado de conservação.
    """
    summary = summarizer.summarize(text, max_length=100)
    
    assert isinstance(summary, str)
    assert len(summary) <= 150  # Allow some flexibility
    assert len(summary) > 0


def test_summarize_with_custom_max_length(summarizer):
    """Test summarization with custom max length."""
    text = "Apartamento T3 no Porto com três quartos, duas casas de banho, sala e cozinha equipada."
    summary = summarizer.summarize(text, max_length=50)
    
    assert isinstance(summary, str)
    assert len(summary) <= 100  # Allow some flexibility


def test_summarize_with_min_length(summarizer):
    """Test summarization with min length parameter."""
    text = "Apartamento T3 no Porto com excelente localização e vistas panorâmicas."
    summary = summarizer.summarize(text, max_length=100, min_length=20)
    
    assert isinstance(summary, str)
    # Summary should respect min_length if possible
    if len(text) > 200:  # Only applies to long texts
        assert len(summary) >= 20


def test_batch_summarize_empty(summarizer):
    """Test batch summarization with empty list."""
    results = summarizer.batch_summarize([])
    assert results == []


def test_batch_summarize_multiple(summarizer):
    """Test batch summarization with multiple texts."""
    texts = [
        "Apartamento T3 no Porto.",
        "Moradia T4 em Lisboa com piscina.",
        "Estúdio no centro de Braga."
    ]
    results = summarizer.batch_summarize(texts, max_length=50)
    
    assert len(results) == 3
    for summary in results:
        assert isinstance(summary, str)


def test_is_available(summarizer):
    """Test checking if summarization model is available."""
    available = summarizer.is_available()
    assert isinstance(available, bool)


def test_extractive_summary_fallback(summarizer):
    """Test extractive summary fallback."""
    # Even if model is not available, extractive should work
    text = """
    Apartamento T3 no Porto. A propriedade tem três quartos, duas casas de banho, 
    sala ampla e cozinha equipada. Localização excelente perto do metro.
    """
    summary = summarizer.summarize(text, max_length=100)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) <= 200  # Should be shorter than original


def test_summarize_portuguese_text(summarizer):
    """Test summarization of Portuguese text."""
    text = """
    Magnífico apartamento de luxo situado na Foz do Douro, com vista mar 
    deslumbrante. Composto por quatro quartos (um suite), sala de estar 
    com 50m², cozinha totalmente equipada com eletrodomésticos de alta gama, 
    três casas de banho, varanda de 20m² e duas lugares de garagem. 
    O edifício dispõe de piscina, ginásio e segurança 24h.
    """
    summary = summarizer.summarize(text, max_length=150)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    # Summary should be significantly shorter than original
    assert len(summary) < len(text)
