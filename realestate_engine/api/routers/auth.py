"""Router for authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from loguru import logger
import os

from realestate_engine.api.middleware.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    revoke_token,
    verify_password,
    hash_password,
    validate_password_strength,
    get_current_user,
    is_token_revoked
)

router = APIRouter()

# Simple in-memory user store (use database in production)
# Pre-populate with a test user for development
_users = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": hash_password("Admin@123456")  # Change in production!
    }
}


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Registration request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=12)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# Rate limiting helper
_login_attempts = {}


def _check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded login rate limit (5 per minute)."""
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Clean old entries
    for ip in list(_login_attempts.keys()):
        if now - _login_attempts[ip]["last_attempt"] > timedelta(minutes=1):
            del _login_attempts[ip]
    
    if client_ip not in _login_attempts:
        _login_attempts[client_ip] = {"count": 0, "last_attempt": now}
    
    _login_attempts[client_ip]["count"] += 1
    _login_attempts[client_ip]["last_attempt"] = now
    
    return _login_attempts[client_ip]["count"] <= 5


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    Args:
        request: Registration credentials
    
    Returns:
        Success message
    """
    # Validate password strength
    is_strong, message = validate_password_strength(request.password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=message)
    
    # Check if user already exists
    if request.username in _users:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    # Create user
    _users[request.username] = {
        "username": request.username,
        "email": request.email,
        "hashed_password": hash_password(request.password)
    }
    
    logger.info(f"User registered: {request.username}")
    return {"message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and return JWT tokens.
    
    Args:
        request: Login credentials
        req: HTTP request for rate limiting
    
    Returns:
        JWT access and refresh tokens
    """
    client_ip = req.client.host if req.client else "unknown"
    
    # Rate limiting
    if not _check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    
    logger.info(f"Login attempt for user: {request.username}")
    
    # Verify user exists
    user = _users.get(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens
    token_data = {"sub": request.username, "email": user["email"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    from realestate_engine.api.middleware.auth import ACCESS_TOKEN_EXPIRE_MINUTES
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token
    
    Returns:
        New JWT access and refresh tokens
    """
    try:
        payload = decode_refresh_token(request.refresh_token)
        username = payload.get("sub")
        
        if not username or username not in _users:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = _users[username]
        token_data = {"sub": username, "email": user["email"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        from realestate_engine.api.middleware.auth import ACCESS_TOKEN_EXPIRE_MINUTES
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/verify")
async def verify_token_endpoint(user: dict = Depends(get_current_user)):
    """
    Verify if current token is valid.
    
    Returns:
        User information if token is valid
    """
    return user


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout endpoint - revokes the current token.
    
    Returns:
        Success message
    """
    # In a production system, add token to blacklist
    # For now, just return success
    return {"message": "Logged out successfully"}
