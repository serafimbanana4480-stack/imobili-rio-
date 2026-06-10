"""Router for authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from loguru import logger

from realestate_engine.api.middleware.auth import (
    create_access_token,
    verify_token,
    optional_auth
)
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS
from realestate_engine.utils.config import config

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
@rate_limit(RATE_LIMITS["auth"])
async def login(
    fastapi_request: Request,
    request: LoginRequest
):
    """
    Authenticate user and return JWT token.
    
    Args:
        request: Login credentials
    
    Returns:
        JWT access token
    """
    logger.info(f"Login attempt for user: {request.username}")
    
    # Reject if no admin credentials are configured
    if not config.admin_username:
        raise HTTPException(status_code=401, detail="Authentication not configured")
    
    # Verify username
    if request.username != config.admin_username:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password (supports plain text or hash comparison)
    password_valid = False
    if config.admin_password_hash:
        import hashlib
        provided_hash = hashlib.sha256(request.password.encode()).hexdigest()
        password_valid = provided_hash == config.admin_password_hash
    elif config.admin_password:
        password_valid = request.password == config.admin_password
    else:
        raise HTTPException(status_code=401, detail="Authentication not configured")
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token_data = {"sub": request.username}
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.jwt_access_token_expire_minutes * 60
    )


@router.post("/verify")
async def verify_token_endpoint(user: dict = Depends(optional_auth)):
    """
    Verify if current token is valid.
    
    Returns:
        User information if token is valid
    """
    return user


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    Note: JWT tokens are stateless. Server-side invalidation requires a
    blacklist (e.g., Redis) or very short token expiry. This endpoint exists
    for API completeness; clients should discard the token locally.
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully. Discard token client-side."}
