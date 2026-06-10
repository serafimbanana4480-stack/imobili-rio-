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
        """Calculate CI from multiple valuation estimates.

        Fallback to normal approximation when fewer than 5 values are available.
        """
        if not values:
            return (0, 0)

        import statistics
        mean = statistics.mean(values)
        if len(values) >= 5:
            # Delegate to bootstrap for more robust intervals
            return ConfidenceInterval.from_valuations_bootstrap(values)

        if len(values) > 1:
            std = statistics.stdev(values)
            margin = 1.96 * (std / math.sqrt(len(values)))
        else:
            margin = mean * 0.15

        return (mean - margin, mean + margin)

    @staticmethod
    def from_valuations_bootstrap(values: List[float], n_bootstrap: int = 1000) -> tuple:
        """Calculate CI using bootstrap percentile method.

        More robust for skewed real-estate price distributions.
        """
        if not values or len(values) < 2:
            return ConfidenceInterval.from_valuations(values)

        try:
            import numpy as np
        except ImportError:
            # Fallback to normal approximation if numpy unavailable
            return ConfidenceInterval.from_valuations(values)

        rng = np.random.default_rng(seed=42)
        arr = np.array(values, dtype=float)
        boot_means = []
        n = len(arr)
        for _ in range(n_bootstrap):
            sample = rng.choice(arr, size=n, replace=True)
            boot_means.append(float(np.mean(sample)))

        boot_means.sort()
        lower = boot_means[int(0.025 * n_bootstrap)]
        upper = boot_means[int(0.975 * n_bootstrap)]
        return (lower, upper)
