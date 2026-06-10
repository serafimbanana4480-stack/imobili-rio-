"""FastAPI main application for Real Estate Engine API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
import sys
import signal
from slowapi.middleware import SlowAPIMiddleware

from realestate_engine.api.routers.listings import router as listings_router
from realestate_engine.api.routers.valuation import router as valuation_router
from realestate_engine.api.routers.scoring import router as scoring_router
from realestate_engine.api.routers.health import router as health_router
from realestate_engine.api.routers.explain import router as explain_router
from realestate_engine.api.routers.meta import router as meta_router
from realestate_engine.api.routers.auth import router as auth_router
from realestate_engine.api.middleware.rate_limit import setup_rate_limiting
from realestate_engine.api.middleware.security_headers import SecurityHeadersMiddleware
from realestate_engine.utils.config import config


def setup_signal_handlers():
    """Register signal handlers for graceful shutdown."""
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
docs_url = "/docs" if not config.is_production else None
redoc_url = "/redoc" if not config.is_production else None

app = FastAPI(
    title="Real Estate Engine API",
    description="API for real estate valuation, scoring, and opportunity detection in Portugal",
    version=config.environment,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan
)

# CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api_cors_origins,
    allow_credentials=config.api_allow_credentials and "*" not in config.api_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers after CORS
app.add_middleware(SecurityHeadersMiddleware)

if config.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.trusted_hosts)

# Rate limiting middleware
setup_rate_limiting(app)
app.add_middleware(SlowAPIMiddleware)

# Include routers
if config.api_auth_required:
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(listings_router, prefix="/api/v1/listings", tags=["listings"])
app.include_router(valuation_router, prefix="/api/v1/valuation", tags=["valuation"])
app.include_router(scoring_router, prefix="/api/v1/scoring", tags=["scoring"])
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(explain_router, prefix="/api/v1/explain", tags=["explainability"])
app.include_router(meta_router, prefix="/api/v1/meta", tags=["meta"])

if __name__ == "__main__":
    import uvicorn
    setup_signal_handlers()
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=config.api_bind_host or "127.0.0.1", port=port, log_level="info")
