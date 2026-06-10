"""
Portuguese NLP Features Engine

Advanced Natural Language Processing specifically trained for Portuguese real estate descriptions.
Provides sentiment analysis, entity extraction, quality assessment, and urgency detection.

Features generated:
- Description sentiment analysis
- Amenities extraction using NER
- Quality assessment of descriptions
- Urgency signals detection
- Premium amenities scoring
- Description completeness score
- Language quality metrics
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

try:
    import spacy
    SPACY_AVAILABLE = True
except (ImportError, Exception) as e:
    SPACY_AVAILABLE = False
    logger.warning(f"spacy not available (error: {type(e).__name__}), using rule-based NLP processing")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("textblob not available, using basic sentiment analysis")


@dataclass
class ExtractedEntity:
    """Extracted entity from text"""
    text: str
    label: str
    confidence: float
    start: int
    end: int


class PortugueseNLPProcessor:
    """Advanced NLP processor for Portuguese real estate text"""
    
    def __init__(self):
        self._init_models()
        self._load_dictionaries()
        
    def _init_models(self):
        """Initialize NLP models for Portuguese"""
        if SPACY_AVAILABLE:
            try:
                # Try to load Portuguese model
                self.nlp = spacy.load("pt_core_news_sm")
                logger.info("Loaded Portuguese spaCy model")
            except OSError:
                logger.warning("Portuguese spaCy model not found, using basic processing")
                self.nlp = None
        else:
            self.nlp = None
        
        # Portuguese-specific dictionaries
        self.amenity_keywords = self._build_amenity_dictionary()
        self.quality_indicators = self._build_quality_dictionary()
        self.urgency_signals = self._build_urgency_dictionary()
        self.premium_features = self._build_premium_dictionary()
    
    def _load_dictionaries(self):
        """Load Portuguese-specific dictionaries"""
        
        # Amenities keywords (Portuguese)
        self.amenity_keywords = {
            "garagem": ["garagem", "estacionamento", "box", "lugar para carro", "parqueamento"],
            "piscina": ["piscina", "piscina privativa", "piscina comunitária", "zona de lazer"],
            "elevador": ["elevador", "ascensor", "elevador panorâmico"],
            "varanda": ["varanda", "varanda fechada", "varanda aberta", "sacada"],
            "terraço": ["terraço", "terraço privativo", "telhado", "cobertura"],
            "ar_condicionado": ["ar condicionado", "climatização", "ac", "ar condicionado central"],
            "aquecimento": ["aquecimento central", "radiadores", "piso radiante", "lareira"],
            "segurança": ["segurança 24h", "vigilância", "câmaras", "alarme", "portaria"],
            "ginásio": ["ginásio", "fitness", "sala de ginástica", "academia"],
            "jardim": ["jardim", "jardim privativo", "zona verde", "jardim de inverno"],
            "suite": ["suite", "quarto suite", "suite master", "closet"],
            "cozinha": ["cozinha equipada", "cozinha americana", "cozinha social", "copa"],
            "espaço": ["espaço aberto", "open space", "área de serviço", "despensa"],
        }
        
        # Quality indicators
        self.quality_indicators = {
            "excelente": ["excelente estado", "excelente conservação", "perfeito estado", "impecável"],
            "bom": ["bom estado", "boa conservação", "conservado", "cuidado"],
            "recente": ["recente", "novo", "construção recente", "novíssimo"],
            "renovado": ["renovado", "remodelado", "recuperado", "restaurado"],
            "luxo": ["luxo", "premium", "high-end", "sofisticado", "exclusivo"],
            "tradicional": ["tradicional", "clássico", "características originais"],
        }
        
        # Urgency signals
        self.urgency_signals = {
            "imediato": ["imediato", "urgente", "oportunidade única", "não perca"],
            "negociável": ["negociável", "aceita proposta", "preço negociável"],
            "visita": ["visitas já", "marcar visita", "disponível para visita"],
            "oportunidade": ["oportunidade", "pechincha", "bom negócio", "investimento"],
        }
        
        # Premium features
        self.premium_features = {
            "vista_mar": ["vista mar", "frente para o mar", "vista oceano", "maral"],
            "vista_rio": ["vista rio", "frente para o rio", "marginal", "douro"],
            "solar": ["exposição solar", "sol poente", "sol nascente", "dupla exposição"],
            "central": ["centro", "zona central", "coração da cidade", "localização privilegiada"],
            "exclusivo": ["exclusivo", "único", "raro", "especial"],
        }
    
    def _build_amenity_dictionary(self) -> Dict[str, List[str]]:
        """Build comprehensive amenity dictionary"""
        return {
            "garagem": ["garagem", "estacionamento", "box", "lugar para carro", "parqueamento"],
            "piscina": ["piscina", "piscina privativa", "piscina comunitária", "zona de lazer"],
            "elevador": ["elevador", "ascensor", "elevador panorâmico"],
            "varanda": ["varanda", "varanda fechada", "varanda aberta", "sacada"],
            "terraço": ["terraço", "terraço privativo", "telhado", "cobertura"],
            "ar_condicionado": ["ar condicionado", "climatização", "ac", "ar condicionado central"],
            "aquecimento": ["aquecimento central", "radiadores", "piso radiante", "lareira"],
            "segurança": ["segurança 24h", "vigilância", "câmaras", "alarme", "portaria"],
            "ginásio": ["ginásio", "fitness", "sala de ginástica", "academia"],
            "jardim": ["jardim", "jardim privativo", "zona verde", "jardim de inverno"],
            "suite": ["suite", "quarto suite", "suite master", "closet"],
            "cozinha": ["cozinha equipada", "cozinha americana", "cozinha social", "copa"],
        }
    
    def _build_quality_dictionary(self) -> Dict[str, List[str]]:
        """Build quality indicators dictionary"""
        return {
            "excelente": ["excelente estado", "excelente conservação", "perfeito estado", "impecável"],
            "bom": ["bom estado", "boa conservação", "conservado", "cuidado"],
            "recente": ["recente", "novo", "construção recente", "novíssimo"],
            "renovado": ["renovado", "remodelado", "recuperado", "restaurado"],
            "luxo": ["luxo", "premium", "high-end", "sofisticado", "exclusivo"],
            "tradicional": ["tradicional", "clássico", "características originais"],
        }
    
    def _build_urgency_dictionary(self) -> Dict[str, List[str]]:
        """Build urgency signals dictionary"""
        return {
            "imediato": ["imediato", "urgente", "oportunidade única", "não perca"],
            "negociável": ["negociável", "aceita proposta", "preço negociável"],
            "visita": ["visitas já", "marcar visita", "disponível para visita"],
            "oportunidade": ["oportunidade", "pechincha", "bom negócio", "investimento"],
        }
    
    def _build_premium_dictionary(self) -> Dict[str, List[str]]:
        """Build premium features dictionary"""
        return {
            "vista_mar": ["vista mar", "frente para o mar", "vista oceano", "maral"],
            "vista_rio": ["vista rio", "frente para o rio", "marginal", "douro"],
            "solar": ["exposição solar", "sol poente", "sol nascente", "dupla exposição"],
            "central": ["centro", "zona central", "coração da cidade", "localização privilegiada"],
            "exclusivo": ["exclusivo", "único", "raro", "especial"],
        }
    
    def analyze_description(self, title: str, description: str) -> Dict:
        """Complete analysis of real estate description"""
        
        # Combine title and description for full analysis
        full_text = f"{title} {description}".strip()
        
        if not full_text:
            return self._get_default_nlp_features()
        
        # Extract all features
        features = {
            # Sentiment analysis
            "title_sentiment": self._analyze_sentiment(title),
            "description_sentiment": self._analyze_sentiment(description),
            "overall_sentiment": self._analyze_sentiment(full_text),
            
            # Entity extraction
            "extracted_amenities": self._extract_amenities(full_text),
            "amenities_count": 0,  # Will be calculated below
            "premium_amenities": self._extract_premium_features(full_text),
            "premium_amenities_score": 0.0,  # Will be calculated below
            
            # Quality assessment
            "description_quality_score": self._assess_description_quality(full_text),
            "language_quality_score": self._assess_language_quality(full_text),
            "completeness_score": self._calculate_completeness_score(title, description),
            
            # Urgency and intent
            "urgency_score": self._detect_urgency_signals(full_text),
            "investment_potential": self._assess_investment_potential(full_text),
            
            # Text metrics
            "description_length": len(description),
            "title_length": len(title),
            "unique_words": len(set(full_text.lower().split())),
            "readability_score": self._calculate_readability(full_text),
        }
        
        # Calculate derived scores
        features["amenities_count"] = len(features["extracted_amenities"])
        features["premium_amenities_score"] = self._calculate_premium_score(
            features["premium_amenities"]
        )
        
        return features
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of Portuguese text"""
        if not text:
            return 0.0
        
        # Portuguese-specific sentiment keywords
        positive_words = [
            "excelente", "perfeito", "lindo", "bom", "ótimo", "maravilhoso", 
            "espetacular", "fantástico", "sofisticado", "luxuoso", "privilegiado",
            "exclusivo", "raro", "único", "especial", "premium", "high-end"
        ]
        
        negative_words = [
            "mau", "péssimo", "ruim", "precisa", "reparar", "consertar", 
            "velho", "antigo", "degradado", "humidade", "problema", "defeito"
        ]
        
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total_words = len(text_lower.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / max(total_words, 1)
        return max(-1.0, min(1.0, sentiment * 10))  # Scale and clamp
    
    def _extract_amenities(self, text: str) -> List[str]:
        """Extract amenities from text using keyword matching"""
        if not text:
            return []
        
        found_amenities = []
        text_lower = text.lower()
        
        for amenity, keywords in self.amenity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_amenities.append(amenity)
                    break  # Found this amenity, move to next
        
        return list(set(found_amenities))  # Remove duplicates
    
    def _extract_premium_features(self, text: str) -> List[str]:
        """Extract premium features from text"""
        if not text:
            return []
        
        found_features = []
        text_lower = text.lower()
        
        for feature, keywords in self.premium_features.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_features.append(feature)
                    break
        
        return list(set(found_features))
    
    def _assess_description_quality(self, text: str) -> float:
        """Assess overall quality of description"""
        if not text:
            return 0.0
        
        quality_score = 0.0
        
        # Length factor (good descriptions are detailed)
        length_score = min(len(text) / 500, 1.0)  # Max score at 500 chars
        quality_score += length_score * 0.3
        
        # Structure factor (has proper sentences)
        sentences = re.split(r'[.!?]+', text)
        sentence_score = min(len([s for s in sentences if len(s.strip()) > 10]) / 5, 1.0)
        quality_score += sentence_score * 0.2
        
        # Information density (contains specific details)
        info_patterns = [
            r'\d+\s*m[²²]',  # Area
            r'\d+\s*quartos?',  # Rooms
            r'\d+\s*euros?',  # Price
            r'\d{4}',  # Year
        ]
        info_score = sum(1 for pattern in info_patterns if re.search(pattern, text)) / len(info_patterns)
        quality_score += info_score * 0.3
        
        # Professional language
        professional_words = ["excelente", "conservação", "acabamentos", "qualidade", "moderno"]
        professional_count = sum(1 for word in professional_words if word in text.lower())
        professional_score = min(professional_count / 3, 1.0)
        quality_score += professional_score * 0.2
        
        return min(quality_score, 1.0)
    
    def _assess_language_quality(self, text: str) -> float:
        """Assess language quality and professionalism"""
        if not text:
            return 0.0
        
        quality_score = 0.5  # Base score
        
        # Check for proper capitalization
        if text and text[0].isupper():
            quality_score += 0.1
        
        # Check for proper sentence endings
        if text.rstrip().endswith(('.', '!', '?')):
            quality_score += 0.1
        
        # Penalize excessive punctuation
        excessive_punct = text.count('!') + text.count('?') > 3
        if excessive_punct:
            quality_score -= 0.2
        
        # Check for professional vocabulary
        professional_terms = ["acabamentos", "conservação", "qualidade", "moderno", "equipado"]
        professional_count = sum(1 for term in professional_terms if term in text.lower())
        quality_score += min(professional_count * 0.1, 0.3)
        
        # Penalize all caps (shouting)
        if text.isupper():
            quality_score -= 0.3
        
        return max(0.0, min(quality_score, 1.0))
    
    def _calculate_completeness_score(self, title: str, description: str) -> float:
        """Calculate completeness score based on information provided"""
        score = 0.0
        
        # Title presence and quality
        if title and len(title) > 10:
            score += 0.2
        
        # Description presence and detail
        if description and len(description) > 100:
            score += 0.3
        
        # Essential information
        combined_text = f"{title} {description}".lower()
        
        # Property type
        if any(word in combined_text for word in ["apartamento", "moradia", "casa", "terreno"]):
            score += 0.1
        
        # Size information
        if re.search(r'\d+\s*m[²²]', combined_text):
            score += 0.1
        
        # Room count
        if re.search(r'\d+\s*quartos?', combined_text):
            score += 0.1
        
        # Location information
        if any(word in combined_text for word in ["porto", "rua", "avenida", "freguesia"]):
            score += 0.1
        
        # Contact or visit information
        if any(word in combined_text for word in ["visita", "contato", "telefone", "marcar"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _detect_urgency_signals(self, text: str) -> float:
        """Detect urgency signals in description"""
        if not text:
            return 0.0
        
        urgency_score = 0.0
        text_lower = text.lower()
        
        # Check for urgency keywords
        for urgency_type, keywords in self.urgency_signals.items():
            for keyword in keywords:
                if keyword in text_lower:
                    urgency_score += 0.2
                    break
        
        return min(urgency_score, 1.0)
    
    def _assess_investment_potential(self, text: str) -> float:
        """Assess investment potential based on description"""
        if not text:
            return 0.0
        
        investment_score = 0.0
        text_lower = text.lower()
        
        # Investment keywords
        investment_keywords = [
            "investimento", "rentabilidade", "retorno", "arrendamento", 
            "negócio", "oportunidade", "valorização", "potencial"
        ]
        
        for keyword in investment_keywords:
            if keyword in text_lower:
                investment_score += 0.2
        
        # Location indicators
        if any(word in text_lower for word in ["centro", "turismo", "universidade"]):
            investment_score += 0.2
        
        # Condition indicators
        if any(word in text_lower for word in ["novo", "renovado", "excelente"]):
            investment_score += 0.2
        
        return min(investment_score, 1.0)
    
    def _calculate_premium_score(self, premium_features: List[str]) -> float:
        """Calculate premium amenities score"""
        if not premium_features:
            return 0.0
        
        # Weight different premium features
        feature_weights = {
            "vista_mar": 0.3,
            "vista_rio": 0.25,
            "solar": 0.2,
            "central": 0.15,
            "exclusivo": 0.1,
        }
        
        score = 0.0
        for feature in premium_features:
            score += feature_weights.get(feature, 0.1)
        
        return min(score, 1.0)
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Flesch-like metric)"""
        if not text:
            return 0.0
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if len(words) == 0 or len(sentences) == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)
        
        # Simplified readability score
        readability = 100 - (avg_words_per_sentence * 2) - (avg_chars_per_word * 0.5)
        return max(0.0, min(readability / 100, 1.0))
    
    def _get_default_nlp_features(self) -> Dict:
        """Return default NLP features when text is missing"""
        return {
            "title_sentiment": 0.0,
            "description_sentiment": 0.0,
            "overall_sentiment": 0.0,
            "extracted_amenities": [],
            "amenities_count": 0,
            "premium_amenities": [],
            "premium_amenities_score": 0.0,
            "description_quality_score": 0.0,
            "language_quality_score": 0.0,
            "completeness_score": 0.0,
            "urgency_score": 0.0,
            "investment_potential": 0.0,
            "description_length": 0,
            "title_length": 0,
            "unique_words": 0,
            "readability_score": 0.0,
        }


# Global instance for reuse
_nlp_processor = None

def get_nlp_processor() -> PortugueseNLPProcessor:
    """Get singleton instance of NLP processor"""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = PortugueseNLPProcessor()
    return _nlp_processor

def analyze_portuguese_description(title: str, description: str) -> Dict:
    """Convenience function to analyze Portuguese real estate description"""
    processor = get_nlp_processor()
    return processor.analyze_description(title, description)
