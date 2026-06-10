"""
BERTimbau Integration for Portuguese NLP
Provides BERT-based embeddings and text processing for Portuguese real estate descriptions.
"""

import numpy as np
from typing import Dict, List, Optional
from loguru import logger

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, BERT features will be disabled")


class BERTPortugueseProcessor:
    """BERT-based processor for Portuguese text using BERTimbau model."""
    
    def __init__(self, model_name: str = 'neuralmind/bert-base-portuguese-cased'):
        """
        Initialize the BERT processor.
        
        Args:
            model_name: Hugging Face model name (default: BERTimbau Base)
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        
        if TRANSFORMERS_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load BERT model and tokenizer."""
        try:
            # Check if CPU or GPU is available
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info(f"Loaded BERT model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            self.tokenizer = None
            self.model = None
    
    def get_embeddings(self, text: str, max_length: int = 512) -> Optional[np.ndarray]:
        """
        Get BERT embeddings for text.
        
        Args:
            text: Input text
            max_length: Maximum sequence length
            
        Returns:
            Numpy array of embeddings or None if failed
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            logger.warning("BERT model not available, returning None")
            return None
        
        try:
            # Tokenize text
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                max_length=max_length,
                truncation=True,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Use [CLS] token embedding as sentence representation
            cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return cls_embedding[0]  # Return as 1D array
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            return None
    
    def get_token_embeddings(self, text: str, max_length: int = 512) -> Optional[np.ndarray]:
        """
        Get token-level embeddings for text.
        
        Args:
            text: Input text
            max_length: Maximum sequence length
            
        Returns:
            Numpy array of token embeddings or None if failed
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            return None
        
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
                
            # Return all token embeddings
            embeddings = outputs.last_hidden_state.cpu().numpy()
            return embeddings[0]  # Return as 2D array
        except Exception as e:
            logger.error(f"Failed to get token embeddings: {e}")
            return None
    
    def get_similarity(self, text1: str, text2: str) -> Optional[float]:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1) or None if failed
        """
        emb1 = self.get_embeddings(text1)
        emb2 = self.get_embeddings(text2)
        
        if emb1 is None or emb2 is None:
            return None
        
        try:
            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return None
    
    def batch_get_embeddings(self, texts: List[str], max_length: int = 512) -> List[Optional[np.ndarray]]:
        """
        Get embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            max_length: Maximum sequence length
            
        Returns:
            List of embedding arrays
        """
        embeddings = []
        for text in texts:
            emb = self.get_embeddings(text, max_length)
            embeddings.append(emb)
        return embeddings
    
    def is_available(self) -> bool:
        """Check if BERT model is available."""
        return TRANSFORMERS_AVAILABLE and self.model is not None and self.tokenizer is not None


# Global instance for reuse
_bert_processor = None

def get_bert_processor() -> BERTPortugueseProcessor:
    """Get singleton instance of BERT processor."""
    global _bert_processor
    if _bert_processor is None:
        _bert_processor = BERTPortugueseProcessor()
    return _bert_processor
