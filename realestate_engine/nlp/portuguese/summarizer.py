"""
Description Summarizer for Portuguese Text
Generates concise summaries of real estate descriptions using T5-Portuguese or BART-Portuguese.
"""

from typing import Optional
from loguru import logger

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, summarization will be disabled")


class DescriptionSummarizer:
    """Text summarizer for Portuguese real estate descriptions."""
    
    def __init__(self, model_name: str = 'unicamp-dl/ptt5-base-portuguese-vocab'):
        """
        Initialize the summarizer.
        
        Args:
            model_name: Hugging Face model name for summarization
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self._model_load_failed = False
        
        if TRANSFORMERS_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load summarization model and tokenizer."""
        if self._model_load_failed:
            return
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            
            # Load T5-Portuguese model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Loaded summarization model: {self.model_name}")
        except Exception as e:
            err_type = type(e).__name__
            if "spiece" in str(e).lower() or "sentencepiece" in str(e).lower() or "parsing" in str(e).lower():
                logger.warning(f"Summarizer: tokenizer cache appears corrupted ({err_type}). "
                               f"Clear HuggingFace cache for '{self.model_name}' and retry, "
                               f"or use extractive fallback.")
            else:
                logger.warning(f"Summarizer: model load failed ({err_type}), using extractive fallback")
            self.tokenizer = None
            self.model = None
            self._model_load_failed = True
    
    def summarize(self, text: str, max_length: int = 100, min_length: int = 30) -> Optional[str]:
        """
        Generate summary of text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Summary text or None if failed
        """
        if not text or not text.strip():
            return ""
        
        stripped = text.strip()
        # Short-circuit: text already within target length — return unchanged
        if len(stripped) <= max_length:
            return stripped
        
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            # Fallback to extractive summarization
            return self._extractive_summary(text, max_length)
        
        try:
            # Prepend prefix for T5 models (only for model input)
            model_input = text
            if 't5' in self.model_name.lower():
                model_input = 'summarize: ' + text
            
            inputs = self.tokenizer(
                model_input,
                return_tensors='pt',
                max_length=512,
                truncation=True,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    max_length=max_length,
                    min_length=min_length,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True
                )
            
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            # T5 sometimes echoes the task prefix in the output — strip it
            summary = summary.strip()
            if summary.lower().startswith("summarize:"):
                summary = summary[len("summarize:"):].strip()
            # Guarantee max_length characters (token count != character count)
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
            return summary
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return self._extractive_summary(text, max_length)
    
    def _extractive_summary(self, text: str, max_length: int = 100) -> str:
        """
        Fallback extractive summarization using sentence selection.
        
        Args:
            text: Input text
            max_length: Maximum length of summary
            
        Returns:
            Extracted summary
        """
        import re
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return ""
        
        # Take first 2-3 sentences or until max_length is reached
        summary = ""
        for i, sentence in enumerate(sentences[:3]):
            if len(summary) + len(sentence) + 2 <= max_length:
                summary += sentence + ". "
            else:
                break
        
        summary = summary.strip()
        # Guarantee max_length characters
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        return summary
    
    def batch_summarize(self, texts: list, max_length: int = 100) -> list:
        """
        Generate summaries for multiple texts.
        
        Args:
            texts: List of input texts
            max_length: Maximum length of each summary
            
        Returns:
            List of summary texts
        """
        summaries = []
        for text in texts:
            summary = self.summarize(text, max_length)
            summaries.append(summary)
        return summaries
    
    def is_available(self) -> bool:
        """Check if summarization model is available."""
        return TRANSFORMERS_AVAILABLE and self.model is not None and self.tokenizer is not None


# Global instance for reuse
_summarizer = None

def get_summarizer() -> DescriptionSummarizer:
    """Get singleton instance of summarizer."""
    global _summarizer
    if _summarizer is None:
        _summarizer = DescriptionSummarizer()
    return _summarizer
