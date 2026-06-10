"""JWT Authentication middleware."""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from realestate_engine.utils.config import config

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    if not config.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured before issuing tokens")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    return encoded_jwt


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        Token payload if valid
    
    Raises:
        HTTPException if token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not config.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured",
        )
    try:
        token = credentials.credentials
        # Restrict algorithms to prevent algorithm confusion attacks
        allowed_algorithms = ["HS256", "HS384", "HS512"]
        if config.jwt_algorithm not in allowed_algorithms:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid JWT algorithm configuration",
            )
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """
    Get current user from JWT token.
    
    Note: JWT is stateless — for token revocation (blacklist/logout),
    implement a Redis-backed blacklist or use very short expiry times.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User information from token
    
    Raises:
        HTTPException if token is invalid or user not found
    """
    payload = verify_token(credentials)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": user_id, **payload}


async def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """
    Optional authentication for development.
    
    In development mode, returns a mock user if no token provided.
    In production, requires valid token.
    """
    if not config.api_auth_required and credentials is None:
        return {"user_id": "dev-user"}
    return await get_current_user(credentials)
