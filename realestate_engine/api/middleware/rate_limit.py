"""Rate limiting middleware using slowapi."""
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger


def get_client_ip(request: Request) -> str:
    """Extract client IP considering reverse proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


# Initialize rate limiter
limiter = Limiter(key_func=get_client_ip)
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
    "auth": "10/minute",
}
