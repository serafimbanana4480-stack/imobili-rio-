"""
Advanced Sentiment Analyzer for Portuguese Text
Uses BERT-based models for sentiment analysis of Portuguese real estate descriptions.
"""

import numpy as np
from typing import Dict, Optional
from loguru import logger

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, BERT sentiment will be disabled")


class SentimentAnalyzer:
    """Sentiment analyzer for Portuguese real estate text.

    Uses rule-based analysis by default.  A fine-tuned BERT checkpoint can
    be loaded by passing its HF id / local path as *model_name*, but the
    generic ``neuralmind/bert-base-portuguese-cased`` is **not** a sentiment
    model — loading it as ``AutoModelForSequenceClassification`` produces
    random classifier weights and garbage predictions.
    """

    # The base BERTimbau is NOT fine-tuned for classification.  Only load
    # BERT when a genuinely fine-tuned model id is supplied.
    _BASE_MODELS_SKIP = {
        'neuralmind/bert-base-portuguese-cased',
        'neuralmind/bert-large-portuguese-cased',
    }

    def __init__(self, model_name: str = 'neuralmind/bert-base-portuguese-cased'):
        """
        Initialize the sentiment analyzer.
        
        Args:
            model_name: Hugging Face model name for sentiment analysis
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self.labels = ['negative', 'neutral', 'positive']
        
        if TRANSFORMERS_AVAILABLE and model_name not in self._BASE_MODELS_SKIP:
            self._load_model()
        elif model_name in self._BASE_MODELS_SKIP:
            logger.info("Sentiment: skipping base BERTimbau (not fine-tuned for classification) — using rule-based")
    
    def _load_model(self):
        """Load sentiment model and tokenizer."""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            
            # Note: For actual sentiment analysis, you would use a fine-tuned model
            # For now, we'll use the base BERTimbau model as a placeholder
            # In production, replace with: 'neuralmind/bert-base-portuguese-cased-sentiment'
            # or a custom fine-tuned model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, 
                num_labels=3  # negative, neutral, positive
            )
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Loaded sentiment model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            self.tokenizer = None
            self.model = None
    
    def analyze_sentiment(self, text: str, max_length: int = 512) -> Dict:
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text
            max_length: Maximum sequence length
            
        Returns:
            Dictionary with sentiment score and label
        """
        if not text or not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'probabilities': {'negative': 0.0, 'neutral': 1.0, 'positive': 0.0}
            }
        
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            # Fallback to rule-based sentiment
            return self._rule_based_sentiment(text)
        
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
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
            
            # Get predicted class and probabilities
            probs = probabilities[0].cpu().numpy()
            predicted_class = np.argmax(probs)
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = (probs[2] - probs[0])  # positive - negative
            
            return {
                'sentiment_score': float(sentiment_score),
                'sentiment_label': self.labels[predicted_class],
                'confidence': float(probs[predicted_class]),
                'probabilities': {
                    'negative': float(probs[0]),
                    'neutral': float(probs[1]),
                    'positive': float(probs[2])
                }
            }
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict:
        """
        Fallback rule-based sentiment analysis.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment info
        """
        text_lower = text.lower()
        
        # Portuguese sentiment keywords
        positive_words = [
            'excelente', 'perfeito', 'lindo', 'bom', 'ótimo', 'maravilhoso',
            'espetacular', 'fantástico', 'sofisticado', 'luxuoso', 'privilegiado',
            'exclusivo', 'raro', 'único', 'especial', 'premium', 'moderno',
            'renovado', 'novo', 'impecável', 'conservado'
        ]
        
        negative_words = [
            'mau', 'péssimo', 'ruim', 'precisa', 'reparar', 'consertar',
            'velho', 'antigo', 'degradado', 'humidade', 'problema', 'defeito',
            'obras', 'intervenção', 'arranjos'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0.0
            label = 'neutral'
        elif positive_count > negative_count:
            sentiment_score = positive_count / total
            label = 'positive'
        elif negative_count > positive_count:
            sentiment_score = -negative_count / total
            label = 'negative'
        else:
            sentiment_score = 0.0
            label = 'neutral'
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': label,
            'confidence': min(total / 5.0, 1.0),
            'probabilities': {
                'negative': 1.0 - sentiment_score if sentiment_score < 0 else 0.0,
                'neutral': 0.5,
                'positive': sentiment_score if sentiment_score > 0 else 0.0
            }
        }
    
    def batch_analyze(self, texts: list) -> list:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of sentiment dictionaries
        """
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        return results
    
    def is_available(self) -> bool:
        """Check if sentiment model is available."""
        return TRANSFORMERS_AVAILABLE and self.model is not None and self.tokenizer is not None


# Global instance for reuse
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get singleton instance of sentiment analyzer."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
