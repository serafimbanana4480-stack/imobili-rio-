"""Confidence interval calculation for valuations."""
import math
from typing import Optional, List
from loguru import logger


class ConfidenceInterval:
    """Calculates confidence intervals for valuations."""
    
    @staticmethod
    def calculate(value: float, std_error: Optional[float] = None, confidence: float = 0.95) -> tuple:
        """Calculate confidence interval."""
        if std_error is None or std_error <= 0:
            # Default: +/- 15% of value
            margin = value * 0.15
            return (value - margin, value + margin)
        
        # Z-score for 95% confidence = 1.96
        z = 1.96 if confidence == 0.95 else 1.645 if confidence == 0.90 else 2.576
        margin = z * std_error
        return (value - margin, value + margin)
    
    @staticmethod
    def from_valuations(values: List[float]) -> tuple:
        """Calculate CI from multiple valuation estimates."""
        if not values:
            return (0, 0)
        
        import statistics
        mean = statistics.mean(values)
        if len(values) > 1:
            std = statistics.stdev(values)
            margin = 1.96 * (std / math.sqrt(len(values)))
        else:
            margin = mean * 0.15
        
        return (mean - margin, mean + margin)
