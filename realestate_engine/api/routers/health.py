"""Router for health check endpoints."""
from fastapi import APIRouter
from loguru import logger
import sys

sys.path.insert(0, '..')

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "Real Estate Engine API",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status.
    
    Returns:
        Detailed health status
    """
    components = {
        "api": "healthy",
        "database": "unknown",
        "valuation_engine": "unknown",
        "scoring_engine": "unknown"
    }
    
    # Check database connection
    try:
        from realestate_engine.database.repository import DatabaseRepository
        repo = DatabaseRepository()
        repo.get_clean_listings(limit=1)
        components["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        components["database"] = "unhealthy"
    
    # Check valuation engine
    try:
        from realestate_engine.valuation.valuation_engine import ValuationEngine
        engine = ValuationEngine()
        components["valuation_engine"] = "healthy"
    except Exception as e:
        logger.warning(f"Valuation engine health check failed: {e}")
        components["valuation_engine"] = "unhealthy"
    
    # Check scoring engine
    try:
        from realestate_engine.scoring.scoring_engine import ScoringEngine
        engine = ScoringEngine()
        components["scoring_engine"] = "healthy"
    except Exception as e:
        logger.warning(f"Scoring engine health check failed: {e}")
        components["scoring_engine"] = "unhealthy"
    
    overall_status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
    
    return {
        "status": overall_status,
        "service": "Real Estate Engine API",
        "version": "1.0.0",
        "components": components
    }
