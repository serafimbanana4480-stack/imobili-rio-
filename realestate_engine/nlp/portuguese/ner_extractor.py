"""
Named Entity Recognition (NER) Extractor for Portuguese Text
Extracts entities like locations, amenities, property types from Portuguese real estate descriptions.
"""

import re
from typing import Dict, List, Optional
from loguru import logger

import numpy as np

try:
    from transformers import AutoModelForTokenClassification, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, BERT NER will use rule-based extraction")


class NERExtractor:
    """NER extractor for Portuguese real estate text.

    Uses rule-based extraction by default.  The generic BERTimbau base
    model is NOT fine-tuned for token classification — loading it as
    ``AutoModelForTokenClassification`` produces random classifier weights.
    Only load BERT when a genuinely fine-tuned NER model id is supplied.
    """

    _BASE_MODELS_SKIP = {
        'neuralmind/bert-base-portuguese-cased',
        'neuralmind/bert-large-portuguese-cased',
    }

    def __init__(self, model_name: str = 'neuralmind/bert-base-portuguese-cased'):
        """
        Initialize the NER extractor.
        
        Args:
            model_name: Hugging Face model name for NER
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        
        # Entity labels for real estate
        self.entity_labels = {
            'LOC': 'Location',
            'AMENITY': 'Amenity',
            'PROPERTY_TYPE': 'Property Type',
            'FEATURE': 'Feature',
            'CONDITION': 'Condition'
        }
        
        if TRANSFORMERS_AVAILABLE and model_name not in self._BASE_MODELS_SKIP:
            self._load_model()
        elif model_name in self._BASE_MODELS_SKIP:
            logger.info("NER: skipping base BERTimbau (not fine-tuned for token classification) — using rule-based")
    
    def _load_model(self):
        """Load NER model and tokenizer."""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            
            # Note: For actual NER, you would use a fine-tuned model
            # For now, we'll use the base BERTimbau model as a placeholder
            # In production, replace with a custom fine-tuned NER model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.entity_labels)
            )
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Loaded NER model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            self.tokenizer = None
            self.model = None
    
    def extract_entities(self, text: str, max_length: int = 512) -> List[Dict]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            max_length: Maximum sequence length
            
        Returns:
            List of entity dictionaries
        """
        if not text or not text.strip():
            return []
        
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            # Fallback to rule-based extraction
            return self._rule_based_extraction(text)
        
        try:
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                max_length=max_length,
                truncation=True,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=-1)
            
            # Convert predictions to entities
            tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
            entities = self._parse_entities(tokens, predictions[0].cpu().numpy())
            
            return entities
        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            return self._rule_based_extraction(text)
    
    def _parse_entities(self, tokens: List[str], predictions: np.ndarray) -> List[Dict]:
        """Parse token predictions into entities."""
        entities = []
        current_entity = None
        
        for token, pred in zip(tokens, predictions):
            if token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
            
            # Simplified parsing - in production, use proper BIO tagging
            label_idx = pred % len(self.entity_labels)
            label = list(self.entity_labels.keys())[label_idx]
            
            if current_entity and current_entity['label'] == label:
                current_entity['text'] += token.replace('##', '')
            else:
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    'text': token.replace('##', ''),
                    'label': label,
                    'label_name': self.entity_labels[label],
                    'confidence': 0.8
                }
        
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    def _rule_based_extraction(self, text: str) -> List[Dict]:
        """
        Fallback rule-based entity extraction.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        text_lower = text.lower()
        
        # Location patterns
        location_patterns = [
            r'\bporto\b', r'\blisboa\b', r'\bbraga\b', r'\bcoimbra\b',
            r'\bfaro\b', r'\baveiro\b', r'\bviseu\b', r'\bleiria\b',
            r'\bsantarém\b', r'\bsetúbal\b', r'\bévora\b', r'\bguarda\b',
            r'\bcastelo branco\b', r'\bportalegre\b', r'\bvila real\b',
            r'\bbragança\b', r'\bviana do castelo\b', r'\bmadeira\b',
            r'\bacores\b', r'\bavenida\b', r'\brua\b', r'\bpraça\b',
            r'\blargo\b', r'\bquinta\b', r'\bherdade\b'
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'LOC',
                    'label_name': 'Location',
                    'confidence': 0.7
                })
        
        # Property type patterns
        property_patterns = [
            r'\bapartamento\b', r'\bmoradia\b', r'\bcasa\b', r'\bterreno\b',
            r'\bloft\b', r'\bestúdio\b', r'\bquinta\b', r'\bherdade\b',
            r'\bvivenda\b', r'\bt[0-9]\b', r'\bt[0-9][0-9]\b'
        ]
        
        for pattern in property_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'PROPERTY_TYPE',
                    'label_name': 'Property Type',
                    'confidence': 0.8
                })
        
        # Amenity patterns
        amenity_patterns = {
            'garagem': r'\bgarag[eé]m\b',
            'piscina': r'\bpiscina\b',
            'elevador': r'\belevador\b',
            'varanda': r'\bvaranda\b',
            'terraço': r'\bterra[çc]o\b',
            'jardim': r'\bjardim\b',
            'ar condicionado': r'\bar\s+condicionado\b',
            'aquecimento': r'\baquecimento\b'
        }
        
        for amenity, pattern in amenity_patterns.items():
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'AMENITY',
                    'label_name': 'Amenity',
                    'confidence': 0.9
                })
        
        # Condition patterns
        condition_patterns = {
            'novo': r'\bnovo\b',
            'renovado': r'\brenovado\b',
            'remodelado': r'\bremodelado\b',
            'excelente estado': r'\bexcelente\s+estado\b',
            'bom estado': r'\bbom\s+estado\b',
            'precisa obras': r'\bprecisa\s+obras\b'
        }
        
        for condition, pattern in condition_patterns.items():
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'CONDITION',
                    'label_name': 'Condition',
                    'confidence': 0.85
                })
        
        return entities
    
    def extract_entities_by_type(self, text: str, entity_type: str) -> List[str]:
        """
        Extract entities of a specific type.
        
        Args:
            text: Input text
            entity_type: Type of entity to extract (LOC, AMENITY, etc.)
            
        Returns:
            List of entity texts
        """
        all_entities = self.extract_entities(text)
        return [e['text'] for e in all_entities if e['label'] == entity_type]
    
    def batch_extract(self, texts: list) -> list:
        """
        Extract entities from multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of entity lists
        """
        results = []
        for text in texts:
            entities = self.extract_entities(text)
            results.append(entities)
        return results
    
    def is_available(self) -> bool:
        """Check if NER model is available."""
        return TRANSFORMERS_AVAILABLE and self.model is not None and self.tokenizer is not None


# Global instance for reuse
_ner_extractor = None

def get_ner_extractor() -> NERExtractor:
    """Get singleton instance of NER extractor."""
    global _ner_extractor
    if _ner_extractor is None:
        _ner_extractor = NERExtractor()
    return _ner_extractor
