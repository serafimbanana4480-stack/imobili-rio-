"""Rate limiting middleware using slowapi."""
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app_limiter = None  # Will be set in main.py


def setup_rate_limiting(app):
    """Setup rate limiting for the FastAPI app."""
    global app_limiter
    app_limiter = limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Rate limit decorators
def rate_limit(limit: str):
    """Rate limit decorator."""
    return limiter.limit(limit)


# Common rate limits
RATE_LIMITS = {
    "default": "100/hour",
    "strict": "10/minute",
    "valuation": "20/hour",
    "scoring": "30/hour",
    "listings": "200/hour",
}
