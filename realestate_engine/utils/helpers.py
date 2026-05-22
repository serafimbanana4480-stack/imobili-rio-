"""General helper functions."""
from typing import List, Any, Optional, Dict
import hashlib
import json


class Helpers:
    """Shared helper functions."""

    @staticmethod
    def generate_hash(data: Any) -> str:
        """Generate consistent hash for data (used for deduplication)."""
        if isinstance(data, str):
            data_str = data
        elif isinstance(data, dict):
            # Sort keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, (list, tuple)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()

    @staticmethod
    def safe_get(d: Dict, keys: List[str], default: Any = None) -> Any:
        """Safely get nested dictionary value using list of keys."""
        if not d or not keys:
            return default
        
        result = d
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, (list, tuple)) and isinstance(key, int):
                result = result[key] if 0 <= key < len(result) else default
            else:
                return default
            
            if result is None:
                return default
        
        return result

    @staticmethod
    def chunk_list(items: List, chunk_size: int) -> List[List]:
        """Split list into chunks of specified size."""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]

    @staticmethod
    def flatten_list(nested_list: List) -> List:
        """Flatten nested lists."""
        result = []
        for item in nested_list:
            if isinstance(item, list):
                result.extend(Helpers.flatten_list(item))
            else:
                result.append(item)
        return result

    @staticmethod
    def clean_string(s: Optional[str]) -> str:
        """Clean string by removing extra whitespace and special characters."""
        if not s:
            return ""
        
        # Remove extra whitespace
        s = ' '.join(s.split())
        
        return s.strip()

    @staticmethod
    def truncate_string(s: Optional[str], max_length: int, suffix: str = "...") -> str:
        """Truncate string to max length with suffix."""
        if not s:
            return ""
        
        if len(s) <= max_length:
            return s
        
        return s[:max_length - len(suffix)] + suffix

    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries recursively."""
        result = {}
        for d in dicts:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = Helpers.merge_dicts(result[key], value)
                else:
                    result[key] = value
        return result

    @staticmethod
    def percentage_of(part: float, total: float) -> Optional[float]:
        """Calculate percentage safely."""
        if total == 0:
            return None
        
        return (part / total) * 100

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely divide with default on division by zero."""
        if denominator == 0:
            return default
        
        return numerator / denominator

    @staticmethod
    def round_to_decimal(value: float, decimals: int = 2) -> float:
        """Round value to specified decimal places."""
        return round(value, decimals)

    @staticmethod
    def is_empty(value: Any) -> bool:
        """Check if value is empty (None, empty string, empty list, etc.)."""
        if value is None:
            return True
        
        if isinstance(value, (str, list, dict, tuple, set)):
            return len(value) == 0
        
        return False

    @staticmethod
    def remove_duplicates(items: List, key_func: Optional[callable] = None) -> List:
        """Remove duplicates from list while preserving order."""
        seen = set()
        result = []
        
        for item in items:
            key = key_func(item) if key_func else item
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result

    @staticmethod
    def batch_process(items: List, batch_size: int, process_func: callable) -> List[Any]:
        """Process items in batches."""
        results = []
        for batch in Helpers.chunk_list(items, batch_size):
            batch_results = process_func(batch)
            results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
        return results
