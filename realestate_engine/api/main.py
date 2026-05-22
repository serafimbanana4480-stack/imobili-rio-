"""FastAPI main application for Real Estate Engine API."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
import sys
import signal
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Imports rely on PYTHONPATH or package installation; do not manipulate sys.path

from realestate_engine.api.routers.listings import router as listings_router
from realestate_engine.api.routers.valuation import router as valuation_router
from realestate_engine.api.routers.scoring import router as scoring_router
from realestate_engine.api.routers.health import router as health_router
# Auth router removed - system is for internal use only
# from realestate_engine.api.routers.auth import router as auth_router
from realestate_engine.api.middleware.rate_limit import limiter

# Add signal handlers for graceful shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Real Estate Engine API starting up...")
    from realestate_engine.database.models import init_db
    from realestate_engine.utils.config import config
    
    # Initialize database tables
    init_db(config.database_url)
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Real Estate Engine API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Real Estate Engine API",
    description="API for real estate valuation, scoring, and opportunity detection in Portugal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware — restrict origins in production via CORS_ORIGINS env var
_cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if _cors_origins == ["*"]:
    logger.warning("CORS is set to allow all origins ('*'). Set CORS_ORIGINS env var for production.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Include routers
# Authentication router removed - system is for internal use only
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(listings_router, prefix="/api/v1/listings", tags=["listings"])
app.include_router(valuation_router, prefix="/api/v1/valuation", tags=["valuation"])
app.include_router(scoring_router, prefix="/api/v1/scoring", tags=["scoring"])
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
