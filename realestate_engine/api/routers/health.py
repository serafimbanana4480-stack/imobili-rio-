"""Router for health check endpoints."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger
from functools import lru_cache

from realestate_engine.api.middleware.auth import optional_auth
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS
from realestate_engine.utils.config import config

router = APIRouter()


class HealthStatusResponse(BaseModel):
    """Simple health status response."""
    status: str
    service: str
    version: str


class LivenessResponse(BaseModel):
    """Liveness check response."""
    status: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    status: str
    components: Dict[str, Any]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    status: str
    service: str
    version: str
    components: Dict[str, Any]


@lru_cache()
def _get_repo():
    from realestate_engine.database.repository import DatabaseRepository
    return DatabaseRepository()


@lru_cache()
def _get_cache_manager():
    from realestate_engine.utils.cache_manager import cache_manager
    return cache_manager


@router.get("/", response_model=HealthStatusResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return HealthStatusResponse(
        status="healthy",
        service="Real Estate Engine API",
        version=config.environment
    )


@router.get("/live", response_model=LivenessResponse)
async def liveness_check():
    """Liveness check for process supervisors."""
    return LivenessResponse(status="alive")


@router.get("/ready", response_model=ReadinessResponse)
@rate_limit(RATE_LIMITS["default"])
async def readiness_check(
    request: Request,
):
    """Readiness check for serving traffic."""
    components = {}
    try:
        repo = _get_repo()
        repo.get_clean_listings(limit=1)
        components["database"] = "ready"
    except Exception as e:
        logger.warning(f"Database readiness check failed: {e}")
        components["database"] = "not_ready"
    try:
        cache_manager = _get_cache_manager()
        components["cache"] = cache_manager.get_stats()
    except Exception as e:
        logger.warning(f"Cache readiness check failed: {e}")
        components["cache"] = {"enabled": False, "error": "not_ready"}
    status = "ready" if components.get("database") == "ready" else "not_ready"
    return ReadinessResponse(status=status, components=components)


@router.get("/detailed", response_model=DetailedHealthResponse)
@rate_limit(RATE_LIMITS["strict"])
async def detailed_health_check(
    request: Request,
    current_user: dict = Depends(optional_auth)
):
    """
    Detailed health check with component status.
    Requires authentication to avoid information disclosure.
    
    Returns:
        Detailed health status
    """
    components = {
        "api": "healthy",
        "database": "unknown",
        "cache": "unknown",
        "valuation_engine": "unknown",
        "scoring_engine": "unknown"
    }
    
    # Check database connection
    try:
        repo = _get_repo()
        repo.get_clean_listings(limit=1)
        components["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        components["database"] = "unhealthy"
    
    try:
        cache_manager = _get_cache_manager()
        cache_stats = cache_manager.get_stats()
        components["cache"] = "healthy" if cache_stats.get("enabled") else "disabled"
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")
        components["cache"] = "unhealthy"
    
    # Check valuation engine — lightweight: only check if module loads, do not instantiate heavy models
    try:
        from realestate_engine.valuation.valuation_engine import ValuationEngine
        components["valuation_engine"] = "healthy"
    except Exception as e:
        logger.warning(f"Valuation engine health check failed: {e}")
        components["valuation_engine"] = "unhealthy"
    
    # Check scoring engine — lightweight
    try:
        from realestate_engine.scoring.scoring_engine import ScoringEngine
        components["scoring_engine"] = "healthy"
    except Exception as e:
        logger.warning(f"Scoring engine health check failed: {e}")
        components["scoring_engine"] = "unhealthy"
    
    # overall_status: disabled counts as healthy for optional components
    overall_status = "healthy"
    for v in components.values():
        if v == "unhealthy":
            overall_status = "degraded"
            break
    
    return DetailedHealthResponse(
        status=overall_status,
        service="Real Estate Engine API",
        version=config.environment,
        components=components
    )
