"""JWT Authentication middleware."""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
import jwt
from datetime import datetime, timedelta, timezone
import os
import secrets
import hashlib
from passlib.context import CryptContext

security = HTTPBearer()

# Production-ready JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    logger.error("JWT_SECRET_KEY not set in environment. Generate with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    raise ValueError("JWT_SECRET_KEY must be set in environment")

REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", SECRET_KEY)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple in-memory token blacklist (use Redis in production)
_token_blacklist = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength.
    
    Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least 1 uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least 1 lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least 1 number"
    
    if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        return False, "Password must contain at least 1 special character"
    
    return True, "Password is strong"


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_refresh_token(token: str) -> dict:
    """Decode and validate refresh token."""
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def revoke_token(token: str):
    """Revoke a token by adding it to the blacklist."""
    jti = _get_token_jti(token)
    if jti:
        _token_blacklist.add(jti)


def is_token_revoked(token: str) -> bool:
    """Check if a token is in the blacklist."""
    jti = _get_token_jti(token)
    return jti in _token_blacklist if jti else False


def _get_token_jti(token: str) -> str:
    """Extract JTI from token without full verification."""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("jti", "")
    except:
        return ""


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        Token payload if valid
    
    Raises:
        HTTPException if token is invalid
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Get current user from JWT token.
    
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


# Optional: For development, allow bypassing auth
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

async def optional_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Optional authentication for development.
    
    In development mode, returns a mock user if no token provided.
    In production, requires valid token.
    """
    if DEV_MODE and credentials is None:
        return {"user_id": "dev-user", "dev_mode": True}
    return await get_current_user(credentials)
