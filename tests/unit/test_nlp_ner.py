"""Unit tests for NER Extractor."""
import pytest

pytest.importorskip("transformers", reason="transformers not installed (heavy NLP extras)")
pytest.importorskip("torch", reason="torch not installed (heavy NLP extras)")

from realestate_engine.nlp.portuguese.ner_extractor import NERExtractor


@pytest.fixture
def extractor():
    """Create an NERExtractor instance."""
    return NERExtractor()


def test_extractor_initialization(extractor):
    """Test that extractor initializes correctly."""
    assert extractor.model_name == 'neuralmind/bert-base-portuguese-cased'
    assert 'LOC' in extractor.entity_labels
    assert 'AMENITY' in extractor.entity_labels
    assert 'PROPERTY_TYPE' in extractor.entity_labels


def test_extract_entities_empty_text(extractor):
    """Test entity extraction with empty text."""
    entities = extractor.extract_entities("")
    assert entities == []


def test_extract_entities_none_text(extractor):
    """Test entity extraction with None text."""
    entities = extractor.extract_entities(None)
    assert entities == []


def test_extract_entities_location(extractor):
    """Test entity extraction for locations."""
    text = "Apartamento localizado no Porto, na Rua de Santa Catarina."
    entities = extractor.extract_entities(text)
    
    # Should extract at least some entities (may be LOC or other types)
    # Rule-based extraction should find "Porto" as a location
    assert isinstance(entities, list)
    # Check if any location entities were found
    location_entities = [e for e in entities if e['label'] == 'LOC']
    # If model is available, it might find locations; otherwise rule-based should
    if extractor.is_available():
        # Model-based extraction - may or may not find locations
        pass
    else:
        # Rule-based should find at least "Porto"
        assert len(location_entities) >= 1


def test_extract_entities_property_type(extractor):
    """Test entity extraction for property types."""
    text = "Venda de apartamento T3 com moradia T4."
    entities = extractor.extract_entities(text)
    
    # Should extract property type entities (rule-based should work)
    property_entities = [e for e in entities if e['label'] == 'PROPERTY_TYPE']
    if not extractor.is_available():
        # Rule-based extraction should find property types
        assert len(property_entities) >= 1
    else:
        # Model-based - just check it returns something
        assert isinstance(entities, list)


def test_extract_entities_amenities(extractor):
    """Test entity extraction for amenities."""
    text = "Apartamento com garagem, piscina e jardim."
    entities = extractor.extract_entities(text)
    
    # Should extract amenity entities (rule-based should work)
    amenity_entities = [e for e in entities if e['label'] == 'AMENITY']
    if not extractor.is_available():
        # Rule-based extraction should find amenities
        assert len(amenity_entities) >= 1
    else:
        # Model-based - just check it returns something
        assert isinstance(entities, list)


def test_extract_entities_condition(extractor):
    """Test entity extraction for condition."""
    text = "Apartamento novo, totalmente renovado em excelente estado."
    entities = extractor.extract_entities(text)
    
    # Should extract condition entities (rule-based should work)
    condition_entities = [e for e in entities if e['label'] == 'CONDITION']
    if not extractor.is_available():
        # Rule-based extraction should find conditions
        assert len(condition_entities) >= 1
    else:
        # Model-based - just check it returns something
        assert isinstance(entities, list)


def test_extract_entities_structure(extractor):
    """Test that extracted entities have correct structure."""
    text = "Apartamento no Porto com garagem."
    entities = extractor.extract_entities(text)
    
    if entities:
        entity = entities[0]
        assert 'text' in entity
        assert 'label' in entity
        assert 'label_name' in entity
        assert 'confidence' in entity
        assert isinstance(entity['text'], str)
        assert isinstance(entity['confidence'], float)


def test_extract_entities_by_type_location(extractor):
    """Test extracting entities by specific type."""
    text = "Apartamento em Lisboa com vista para o rio."
    locations = extractor.extract_entities_by_type(text, 'LOC')
    
    assert isinstance(locations, list)
    # Rule-based should find at least one location
    if not extractor.is_available():
        assert len(locations) >= 1


def test_extract_entities_by_type_amenity(extractor):
    """Test extracting amenity entities by type."""
    text = "Apartamento com elevador e ar condicionado."
    amenities = extractor.extract_entities_by_type(text, 'AMENITY')
    
    assert isinstance(amenities, list)
    # Rule-based should find amenities
    if not extractor.is_available():
        # Rule-based extraction should find at least one amenity
        assert len(amenities) >= 1


def test_extract_entities_by_type_invalid_type(extractor):
    """Test extracting entities with invalid type."""
    text = "Apartamento no Porto."
    entities = extractor.extract_entities_by_type(text, 'INVALID_TYPE')
    
    assert entities == []


def test_batch_extract_empty(extractor):
    """Test batch extraction with empty list."""
    results = extractor.batch_extract([])
    assert results == []


def test_batch_extract_multiple(extractor):
    """Test batch extraction with multiple texts."""
    texts = [
        "Apartamento no Porto",
        "Moradia em Lisboa com piscina",
        "T3 no centro de Braga"
    ]
    results = extractor.batch_extract(texts)
    
    assert len(results) == 3
    for entities in results:
        assert isinstance(entities, list)


def test_is_available(extractor):
    """Test checking if NER model is available."""
    available = extractor.is_available()
    assert isinstance(available, bool)


def test_rule_based_extraction_fallback(extractor):
    """Test rule-based extraction fallback."""
    # Even if model is not available, rule-based should work
    text = "Apartamento no Porto com garagem"
    entities = extractor.extract_entities(text)
    
    assert isinstance(entities, list)
    # Should extract at least some entities via rules
    assert len(entities) >= 1
