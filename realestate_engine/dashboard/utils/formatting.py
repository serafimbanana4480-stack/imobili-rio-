"""Data formatting utilities for dashboard.

Consistent number formatting across all dashboard views.
"""


def format_currency(value: float, use_k_notation: bool = True) -> str:
    """Format currency value with consistent notation.
    
    Args:
        value: Currency value in EUR
        use_k_notation: If True, use K/M notation for large numbers
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "N/A"
    
    if use_k_notation:
        if value >= 1_000_000:
            return f"{value/1_000_000:.1f}M€"
        elif value >= 1_000:
            return f"{value/1_000:.0f}K€"
    
    # Standard formatting with Portuguese locale (using . as thousands separator)
    return f"{value:,.0f}€".replace(",", ".")


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format percentage value consistently.
    
    Args:
        value: Percentage value (e.g., 0.15 for 15%)
        decimal_places: Number of decimal places to show
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    
    return f"{value * 100:.{decimal_places}f}%"


def format_area(value: float) -> str:
    """Format area value consistently.
    
    Args:
        value: Area in square meters
        
    Returns:
        Formatted area string
    """
    if value is None:
        return "N/A"
    
    return f"{value:.0f}m²"


def format_date(value, format_string: str = "%Y-%m-%d") -> str:
    """Format date value consistently.
    
    Args:
        value: Date value (datetime or string)
        format_string: Date format string
        
    Returns:
        Formatted date string
    """
    if value is None:
        return "N/A"
    
    if isinstance(value, str):
        return value
    
    return value.strftime(format_string)


def format_number(value: float, decimal_places: int = 0) -> str:
    """Format generic number with Portuguese locale.
    
    Args:
        value: Numeric value
        decimal_places: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if value is None:
        return "N/A"
    
    return f"{value:,.{decimal_places}f}".replace(",", ".")


def format_price_per_m2(value: float) -> str:
    """Format price per square meter consistently.
    
    Args:
        value: Price per square meter in EUR
        
    Returns:
        Formatted price/m² string
    """
    if value is None:
        return "N/A"
    
    return f"{value:,.0f}€/m²".replace(",", ".")
