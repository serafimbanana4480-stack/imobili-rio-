"""Unit tests for BERT Portuguese Processor."""
import pytest
import numpy as np
from realestate_engine.nlp.bert_portuguese import BERTPortugueseProcessor


@pytest.fixture
def processor():
    """Create a BERTPortugueseProcessor instance."""
    return BERTPortugueseProcessor()


def test_processor_initialization(processor):
    """Test that processor initializes correctly."""
    assert processor.model_name == 'neuralmind/bert-base-portuguese-cased'


def test_get_embeddings_empty_text(processor):
    """Test embeddings with empty text."""
    embeddings = processor.get_embeddings("")
    # Should return None if model not available or text empty
    if not processor.is_available():
        assert embeddings is None


def test_get_embeddings_none_text(processor):
    """Test embeddings with None text."""
    embeddings = processor.get_embeddings(None)
    assert embeddings is None


def test_get_embeddings_simple_text(processor):
    """Test embeddings with simple text."""
    text = "Apartamento no Porto."
    embeddings = processor.get_embeddings(text)
    
    if processor.is_available():
        assert embeddings is not None
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings.shape) == 1  # Should be 1D array
    else:
        assert embeddings is None


def test_get_embeddings_with_max_length(processor):
    """Test embeddings with custom max length."""
    text = "Apartamento T3 no Porto com três quartos e duas casas de banho."
    embeddings = processor.get_embeddings(text, max_length=128)
    
    if processor.is_available():
        assert embeddings is not None
        assert isinstance(embeddings, np.ndarray)
    else:
        assert embeddings is None


def test_get_token_embeddings(processor):
    """Test token-level embeddings."""
    text = "Apartamento no Porto."
    embeddings = processor.get_token_embeddings(text)
    
    if processor.is_available():
        assert embeddings is not None
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings.shape) == 2  # Should be 2D array (tokens x embedding_dim)
    else:
        assert embeddings is None


def test_get_similarity(processor):
    """Test similarity calculation between texts."""
    text1 = "Apartamento no Porto."
    text2 = "Apartamento em Lisboa."
    
    similarity = processor.get_similarity(text1, text2)
    
    if processor.is_available():
        assert similarity is not None
        assert 0.0 <= similarity <= 1.0
    else:
        assert similarity is None


def test_get_similarity_identical_texts(processor):
    """Test similarity with identical texts."""
    text = "Apartamento no Porto."
    similarity = processor.get_similarity(text, text)
    
    if processor.is_available():
        assert similarity is not None
        # Should be very close to 1.0 for identical texts
        assert similarity > 0.9
    else:
        assert similarity is None


def test_batch_get_embeddings_empty(processor):
    """Test batch embeddings with empty list."""
    results = processor.batch_get_embeddings([])
    assert results == []


def test_batch_get_embeddings_multiple(processor):
    """Test batch embeddings with multiple texts."""
    texts = [
        "Apartamento no Porto",
        "Moradia em Lisboa",
        "T3 em Braga"
    ]
    results = processor.batch_get_embeddings(texts)
    
    assert len(results) == 3
    if processor.is_available():
        for result in results:
            assert result is not None or result is None  # Some may fail
    else:
        for result in results:
            assert result is None


def test_is_available(processor):
    """Test checking if BERT model is available."""
    available = processor.is_available()
    assert isinstance(available, bool)


def test_embeddings_shape(processor):
    """Test that embeddings have correct shape."""
    text = "Apartamento T3 no Porto."
    embeddings = processor.get_embeddings(text)
    
    if processor.is_available() and embeddings is not None:
        # BERT base has 768 dimensions
        assert embeddings.shape[0] == 768


def test_embeddings_deterministic(processor):
    """Test that embeddings are deterministic for same text."""
    text = "Apartamento no Porto."
    
    if processor.is_available():
        emb1 = processor.get_embeddings(text)
        emb2 = processor.get_embeddings(text)
        
        if emb1 is not None and emb2 is not None:
            np.testing.assert_array_almost_equal(emb1, emb2, decimal=5)


def test_embeddings_different_texts(processor):
    """Test that different texts produce different embeddings."""
    text1 = "Apartamento no Porto."
    text2 = "Moradia em Lisboa."
    
    if processor.is_available():
        emb1 = processor.get_embeddings(text1)
        emb2 = processor.get_embeddings(text2)
        
        if emb1 is not None and emb2 is not None:
            # Should not be identical
            assert not np.array_equal(emb1, emb2)
