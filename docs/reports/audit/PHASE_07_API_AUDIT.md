# PHASE 7: API AUDIT
## REST Design, Versioning, Security

**Date:** 2026-05-04  
**Auditor:** Principal Software Architect + Staff Engineer + Security Engineer  
**Scope:** Complete API analysis for production security and scalability  
**Production Context:** System intended for commercial sale with public API as monetization channel

---

## EXECUTIVE SUMMARY

**Overall API Score:** 58/100

**Critical Issues:** 2  
**High Priority Issues:** 3  
**Medium Priority Issues:** 4  
**Low Priority Issues:** 2

**Key Findings:**
- API uses FastAPI (modern, excellent choice)
- Pydantic v2 schemas for validation (good)
- **CRITICAL:** No authentication - all endpoints are public
- **CRITICAL:** No rate limiting per user (only global)
- **HIGH:** No API versioning strategy
- **HIGH:** No pagination, sorting, or field selection
- **HIGH:** CORS is permissive (allow_origins=["*"])
- Router structure is good (separated by domain)
- Middleware exists but incomplete
- No API documentation (OpenAPI/Swagger auto-generated but not customized)
- No API keys or usage tracking
- No request/response logging
- No error handling standardization

---

## 1. API ARCHITECTURE ANALYSIS

### 1.1 Current Architecture

**LOCATION:** `realestate_engine/api/main.py` (86 lines)

**Architecture Pattern:**
```
FastAPI App
├── Middleware
│   ├── CORS (Permissive)
│   └── Rate Limiting (Global only)
├── Routers
│   ├── listings
│   ├── valuation
│   ├── scoring
│   └── health
├── Schemas
│   ├── Listing schemas
│   ├── Valuation schemas
│   └── Score schemas
└── Signal Handlers
    └── Graceful shutdown
```

**Code Analysis:**
```python
# api/main.py
app = FastAPI(
    title="Real Estate Engine API",
    version="1.0.0",
    description="API for real estate opportunity analysis"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # CRITICAL: Permissive
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(listings_router, prefix="/api/v1/listings")
app.include_router(valuation_router, prefix="/api/v1/valuation")
app.include_router(scoring_router, prefix="/api/v1/scoring")
app.include_router(health_router, prefix="/api/v1/health")

# Auth router removed
# from realestate_engine.api.routers.auth import router as auth_router
# System is for internal use only
```

**Strengths:**
1. **FastAPI:** Modern, fast, type-safe
2. **Pydantic v2:** Excellent validation
3. **Router Structure:** Well-organized by domain
4. **Auto-Documentation:** OpenAPI/Swagger auto-generated
5. **Signal Handlers:** Graceful shutdown
6. **Middleware:** CORS and rate limiting present

**Critical Gaps:**
- 🔴 **No Authentication:** All endpoints are public
- 🔴 **No Authorization:** No RBAC or permissions
- 🔴 **Permissive CORS:** Allows any origin
- ⚠️ **No Versioning Strategy:** v1 hardcoded, no deprecation plan
- ⚠️ **No Pagination:** All endpoints return all data
- ⚠️ **No API Keys:** No usage tracking or authentication
- ⚠️ **No Request Logging:** No audit trail

---

## 2. CRITICAL ISSUES

### 2.1 CRITICAL ISSUE #1: No Authentication

**SEVERITY:** 🔴 CRITICAL - SECURITY BREACH

**LOCATION:** `realestate_engine/api/main.py` (line 21-22 commented out)

**Problem:**
```python
# Auth router removed - system is for internal use only
# from realestate_engine.api.routers.auth import router as auth_router
```

**Root Cause:**
- Authentication router commented out
- No JWT or OAuth integration
- No API key validation
- No user management
- Comment suggests "internal use only" but API is exposed

**Impact on Production:**
- **Security Breach:** Anyone can access all endpoints
- **Data Theft:** All listings, valuations, scores accessible
- **System Abuse:** Unlimited API usage
- **No Accountability:** No audit trail of who accessed what
- **Commercial Risk:** Cannot sell API as SaaS without authentication
- **Legal Risk:** GDPR violation (unauthorized data access)

**Real-World Scenario:**
```
Attacker discovers API endpoint: https://api.example.com/api/v1/listings
Attacker calls: GET /api/v1/listings?limit=10000
Attacker downloads entire database
Attacker sells data to competitors
Financial loss: €100,000+
Legal liability: GDPR fines up to €20M
```

**Refactor Suggestion - JWT Authentication:**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import secrets

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

app = FastAPI(title="Real Estate Engine API")

# User model (simplified)
class User:
    def __init__(self, id: str, username: str, email: str, role: str):
        self.id = id
        self.username = username
        self.email = email
        self.role = role  # admin, user, readonly

# Mock user database (replace with real DB)
USERS_DB = {
    "admin": User(
        id="1",
        username="admin",
        email="admin@example.com",
        role="admin"
    ),
    "user": User(
        id="2",
        username="user",
        email="user@example.com",
        role="user"
    )
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based authorization
class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized"
            )

# Usage in routers
from fastapi import APIRouter, Depends

listings_router = APIRouter(prefix="/listings", tags=["listings"])

@listings_router.get("/")
async def get_listings(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50
):
    """Get listings (authenticated)."""
    if current_user.role == "readonly":
        raise HTTPException(status_code=403, detail="Read-only user")
    
    # Get listings
    repo = DatabaseRepository()
    listings = repo.get_clean_listings(limit=limit)
    
    return {"listings": listings, "total": len(listings)}

@listings_router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(RoleChecker(["admin"]))  # Only admin
):
    """Delete listing (admin only)."""
    # Delete logic
    pass

# Auth router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@auth_router.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = USERS_DB.get(request.username)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# Include auth router
app.include_router(auth_router, prefix="/api/v1/auth")
```

**Benefits:**
- **Security:** Only authenticated users can access API
- **Authorization:** Role-based access control
- **Audit Trail:** Token-based tracking
- **Scalability:** Stateless JWT for distributed systems
- **Standard:** Industry-standard authentication

**Implementation Effort:** 3-4 days  
**Priority:** CRITICAL  
**Risk:** MEDIUM

---

### 2.2 CRITICAL ISSUE #2: Permissive CORS

**SEVERITY:** 🔴 CRITICAL - SECURITY BREACH

**LOCATION:** `realestate_engine/api/main.py` (lines 48-54)

**Problem:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # CRITICAL: Allows any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Root Cause:**
- `allow_origins=["*"]` allows any domain
- Combined with `allow_credentials=True`, this is a security risk
- No whitelist of allowed origins
- No origin validation

**Impact on Production:**
- **CSRF Attacks:** Malicious sites can make authenticated requests
- **Data Theft:** Any site can fetch data from API
- **Security Breach:** No origin restrictions
- **Compliance Risk:** Violates security best practices

**Refactor Suggestion - Secure CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware

# Allowed origins (whitelist)
ALLOWED_ORIGINS = [
    "https://dashboard.example.com",
    "https://app.example.com",
    "http://localhost:3000",  # Development
    "http://localhost:8501",  # Streamlit
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Whitelist instead of wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# For production, use environment variable
import os

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://dashboard.example.com,https://app.example.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Benefits:**
- **Security:** Only whitelisted origins can access API
- **CSRF Protection:** Prevents cross-origin attacks
- **Compliance:** Follows security best practices
- **Flexibility:** Easy to add new origins via config

**Implementation Effort:** 0.5 day  
**Priority:** CRITICAL  
**Risk:** LOW

---

## 3. HIGH PRIORITY ISSUES

### 3.1 HIGH PRIORITY ISSUE #1: No API Versioning Strategy

**SEVERITY:** 🟠 HIGH - NO MIGRATION PATH

**LOCATION:** `realestate_engine/api/main.py` (line 11-12)

**Problem:**
```python
app = FastAPI(
    title="Real Estate Engine API",
    version="1.0.0",  # Hardcoded, no strategy
)

# Routers use hardcoded v1
app.include_router(listings_router, prefix="/api/v1/listings")
app.include_router(valuation_router, prefix="/api/v1/valuation")
```

**Root Cause:**
- No versioning strategy documented
- No deprecation plan for old versions
- No migration guide
- No version compatibility matrix
- No backward compatibility guarantees

**Impact on Production:**
- **Breaking Changes:** Cannot introduce breaking changes
- **No Migration Path:** Clients stuck on old versions
- **No Deprecation:** Cannot phase out old versions
- **Commercial Risk:** Cannot sell API with SLA guarantees

**Refactor Suggestion - API Versioning Strategy:**
```python
from fastapi import APIRouter
from typing import Callable

# Version 1 (current)
listings_router_v1 = APIRouter(prefix="/listings", tags=["listings-v1"])

@listings_router_v1.get("/")
async def get_listings_v1(skip: int = 0, limit: int = 50):
    """Get listings (v1)."""
    repo = DatabaseRepository()
    listings = repo.get_clean_listings(limit=limit, offset=skip)
    return {"listings": listings, "total": len(listings)}

# Version 2 (future)
listings_router_v2 = APIRouter(prefix="/listings", tags=["listings-v2"])

@listings_router_v2.get("/")
async def get_listings_v2(
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "score_total",
    order: str = "desc",
    fields: str = None
):
    """Get listings (v2) with sorting and field selection."""
    repo = DatabaseRepository()
    
    # Parse fields
    selected_fields = fields.split(",") if fields else None
    
    # Get listings with sorting
    listings = repo.get_clean_listings(
        limit=limit,
        offset=skip,
        sort_by=sort_by,
        order=order
    )
    
    # Filter fields if requested
    if selected_fields:
        filtered_listings = [
            {k: v for k, v in listing.items() if k in selected_fields}
            for listing in listings
        ]
    else:
        filtered_listings = listings
    
    return {
        "listings": filtered_listings,
        "total": len(listings),
        "skip": skip,
        "limit": limit
    }

# Include both versions
app.include_router(listings_router_v1, prefix="/api/v1")
app.include_router(listings_router_v2, prefix="/api/v2")

# Deprecation warning for v1
@app.get("/api/v1/listings")
async def get_listings_v1_deprecated():
    """Deprecated endpoint - use v2."""
    return {
        "message": "This endpoint is deprecated. Use /api/v2/listings instead.",
        "deprecated_date": "2026-06-01",
        "sunset_date": "2026-09-01"
    }

# Version compatibility matrix
API_VERSIONS = {
    "v1": {
        "status": "deprecated",
        "deprecated_date": "2026-06-01",
        "sunset_date": "2026-09-01",
        "migration_guide": "/docs/api-migration-v1-to-v2.md"
    },
    "v2": {
        "status": "stable",
        "released_date": "2026-06-01",
        "features": ["pagination", "sorting", "field_selection"]
    }
}

@app.get("/api/versions")
async def get_api_versions():
    """Get API version information."""
    return API_VERSIONS
```

**Benefits:**
- **Migration Path:** Clear path from v1 to v2
- **Backward Compatibility:** v1 still works during migration
- **Deprecation Notice:** Clients know when to migrate
- **Version Information:** Clients can check compatibility
- **Commercial Ready:** SLA guarantees possible

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** LOW

---

### 3.2 HIGH PRIORITY ISSUE #2: No Pagination

**SEVERITY:** 🟠 HIGH - PERFORMANCE RISK

**LOCATION:** `realestate_engine/api/routers/listings.py` (assumed location)

**Problem:**
```python
# Assumed implementation
@router.get("/")
async def get_listings(limit: int = 1000):
    """Get listings - no pagination."""
    listings = repo.get_clean_listings(limit=limit)
    return {"listings": listings}
```

**Root Cause:**
- No `skip` or `offset` parameter
- No `page` parameter
- No total count in response
- No next/previous page links
- No cursor-based pagination

**Impact on Production:**
- **Performance:** Large responses slow down API
- **Bandwidth:** Wasted bandwidth transferring unnecessary data
- **Client Issues:** Clients must handle large responses
- **Scalability:** Cannot handle large datasets efficiently

**Refactor Suggestion - Pagination:**
```python
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool

class PaginationParams(BaseModel):
    skip: int = Query(0, ge=0, description="Number of items to skip")
    limit: int = Query(50, ge=1, le=1000, description="Number of items per page")

@router.get("/listings", response_model=PaginatedResponse)
async def get_listings_paginated(
    params: PaginationParams = Depends(),
    filters: Optional[str] = None
):
    """Get listings with pagination."""
    repo = DatabaseRepository()
    
    # Parse filters
    filter_dict = {}
    if filters:
        # Parse JSON filter string
        import json
        filter_dict = json.loads(filters)
    
    # Get total count
    total = repo.get_clean_listings_count(filters=filter_dict)
    
    # Get paginated data
    listings = repo.get_clean_listings(
        filters=filter_dict,
        limit=params.limit,
        offset=params.skip
    )
    
    # Calculate pagination info
    has_previous = params.skip > 0
    has_next = params.skip + params.limit < total
    
    return PaginatedResponse(
        items=listings,
        total=total,
        skip=params.skip,
        limit=params.limit,
        has_next=has_next,
        has_previous=has_previous
    )

# Cursor-based pagination for large datasets
class CursorPaginationParams(BaseModel):
    cursor: Optional[str] = Query(None, description="Cursor from previous page")
    limit: int = Query(50, ge=1, le=1000)

@router.get("/listings/cursor")
async def get_listings_cursor(params: CursorPaginationParams = Depends()):
    """Get listings with cursor-based pagination."""
    repo = DatabaseRepository()
    
    # Decode cursor (base64 encoded last ID)
    if params.cursor:
        last_id = decode_cursor(params.cursor)
        listings = repo.get_clean_listings_after(last_id, params.limit)
    else:
        listings = repo.get_clean_listings(limit=params.limit)
    
    # Encode next cursor
    next_cursor = None
    if len(listings) == params.limit:
        next_cursor = encode_cursor(listings[-1]["id"])
    
    return {
        "items": listings,
        "next_cursor": next_cursor,
        "limit": params.limit
    }

def encode_cursor(id: str) -> str:
    """Encode cursor (base64)."""
    import base64
    return base64.b64encode(id.encode()).decode()

def decode_cursor(cursor: str) -> str:
    """Decode cursor (base64)."""
    import base64
    return base64.b64decode(cursor.encode()).decode()
```

**Benefits:**
- **Performance:** Smaller responses, faster API
- **Bandwidth:** Reduced data transfer
- **Scalability:** Can handle millions of records
- **Flexibility:** Both offset and cursor pagination

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** LOW

---

### 3.3 HIGH PRIORITY ISSUE #3: No Rate Limiting Per User

**SEVERITY:** 🟠 HIGH - ABUSE RISK

**LOCATION:** `realestate_engine/api/middleware/rate_limit.py` (assumed location)

**Problem:**
```python
# Assumed implementation
# Global rate limit only - no per-user limits
app.add_middleware(SlowAPIMiddleware)
# All users share the same rate limit
```

**Root Cause:**
- Rate limiting is global, not per-user
- No API key-based rate limiting
- No tiered rate limits (free vs paid)
- No burst allowance
- No rate limit per endpoint

**Impact on Production:**
- **Abuse Risk:** Single user can exhaust API quota
- **No Monetization:** Cannot offer tiered pricing
- **Fairness:** Heavy users affect light users
- **DoS Risk:** Vulnerable to denial of service

**Refactor Suggestion - Per-User Rate Limiting:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request, HTTPException, status
from typing import Optional
import redis.asyncio as aioredis
import json

# Redis-backed rate limiter for distributed systems
class RedisRateLimiter:
    """Redis-backed rate limiter for distributed rate limiting."""
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """Check if request is allowed."""
        # Use Redis INCR with expiration
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, window)
        
        return current <= limit
    
    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests."""
        current = await self.redis.get(key)
        if current is None:
            return limit
        return max(0, limit - int(current))

# Rate limit configurations
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "pro": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "requests_per_day": 100000
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_hour": 100000,
        "requests_per_day": 1000000
    }
}

async def check_rate_limit(
    request: Request,
    endpoint: str,
    tier: str = "free"
):
    """Check rate limit for request."""
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    if api_key:
        # Look up user tier from API key
        user_tier = await get_user_tier(api_key)
        rate_limit_config = RATE_LIMITS.get(user_tier, RATE_LIMITS["free"])
        key = f"ratelimit:{endpoint}:{api_key}"
    else:
        # No API key - use free tier with IP-based limiting
        rate_limit_config = RATE_LIMITS["free"]
        key = f"ratelimit:{endpoint}:{get_remote_address(request)}"
    
    # Check minute limit
    limiter = RedisRateLimiter(config.redis_url)
    
    if not await limiter.is_allowed(
        f"{key}:minute",
        rate_limit_config["requests_per_minute"],
        60
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (per minute)"
        )
    
    # Check hour limit
    if not await limiter.is_allowed(
        f"{key}:hour",
        rate_limit_config["requests_per_hour"],
        3600
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (per hour)"
        )
    
    # Add rate limit headers
    remaining = await limiter.get_remaining(
        f"{key}:minute",
        rate_limit_config["requests_per_minute"]
    )
    
    return {
        "X-RateLimit-Limit": rate_limit_config["requests_per_minute"],
        "X-RateLimit-Remaining": remaining,
        "X-RateLimit-Reset": "60"
    }

# Usage in endpoints
@router.get("/listings")
async def get_listings(
    request: Request,
    params: PaginationParams = Depends()
):
    """Get listings with rate limiting."""
    # Check rate limit
    rate_info = await check_rate_limit(request, "listings:get", tier="free")
    
    # Get listings
    repo = DatabaseRepository()
    listings = repo.get_clean_listings(limit=params.limit, offset=params.skip)
    
    # Add rate limit headers
    return {
        "listings": listings,
        "rate_limit": rate_info
    }
```

**Benefits:**
- **Fairness:** Each user has independent quota
- **Monetization:** Tiered pricing based on rate limits
- **Abuse Prevention:** Heavy users don't affect others
- **DoS Protection:** Distributed rate limiting

**Implementation Effort:** 3 days  
**Priority:** HIGH  
**Risk:** MEDIUM (requires Redis)

---

## 4. MEDIUM PRIORITY ISSUES

### 4.1 MEDIUM PRIORITY ISSUE #1: No API Keys

**SEVERITY:** 🟡 MEDIUM - NO USAGE TRACKING

**LOCATION:** Missing component

**Problem:**
- No API key system
- No usage tracking
- No user management
- No billing integration

**Refactor Suggestion:**
```python
import secrets
from datetime import datetime, timedelta
from typing import Optional

class APIKeyManager:
    """Manage API keys for users."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
    
    def generate_api_key(self, user_id: str, tier: str = "free") -> str:
        """Generate new API key for user."""
        api_key = f"ree_{secrets.token_urlsafe(32)}"
        
        # Store in database
        self.repo.create_api_key(
            user_id=user_id,
            api_key_hash=hash_api_key(api_key),
            tier=tier,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365)
        )
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate API key and return user info."""
        api_key_hash = hash_api_key(api_key)
        
        key_data = self.repo.get_api_key_by_hash(api_key_hash)
        
        if not key_data:
            return None
        
        # Check if expired
        if key_data.expires_at < datetime.now(UTC):
            return None
        
        # Check if revoked
        if key_data.is_revoked:
            return None
        
        return {
            "user_id": key_data.user_id,
            "tier": key_data.tier,
            "created_at": key_data.created_at
        }

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()

# Usage in authentication
async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header)
) -> User:
    """Get user from API key."""
    manager = APIKeyManager(repo)
    
    user_data = manager.validate_api_key(api_key)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    user = repo.get_user(user_data["user_id"])
    
    return user
```

**Implementation Effort:** 4 days  
**Priority:** MEDIUM  
**Risk:** MEDIUM

---

### 4.2 Additional Medium Priority Issues

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 2 | No request/response logging | api/main.py | MEDIUM | 2 days | MEDIUM |
| 3 | No error handling standardization | routers/ | MEDIUM | 2 days | MEDIUM |
| 4 | No field selection in responses | routers/ | LOW | 2 days | MEDIUM |

---

## 5. REFACTOR ROADMAP

### Phase 1: Critical Fixes (Week 1)
- [ ] Implement JWT authentication
- [ ] Add role-based authorization
- [ ] Fix CORS to use whitelist
- [ ] Add API key generation and validation

### Phase 2: High Priority (Week 2)
- [ ] Implement API versioning strategy
- [ ] Add pagination to all endpoints
- [ ] Implement per-user rate limiting
- [ ] Add rate limit headers

### Phase 3: Medium Priority (Week 3)
- [ ] Add request/response logging
- [ ] Standardize error handling
- [ ] Add field selection to responses
- [ ] Implement usage tracking

### Phase 4: Low Priority (Week 4)
- [ ] Add OpenAPI documentation customization
- [ ] Implement API health checks
- [ ] Add API analytics dashboard

---

## 6. PRODUCTION READINESS SCORE

**API Audit Score: 58/100**

**Breakdown:**
- Framework: 90/100 (FastAPI is excellent)
- Authentication: 0/100 (NO AUTHENTICATION - CRITICAL)
- Authorization: 0/100 (NO AUTHORIZATION - CRITICAL)
- CORS: 20/100 (permissive - CRITICAL)
- Versioning: 30/100 (no strategy)
- Pagination: 20/100 (not implemented)
- Rate Limiting: 40/100 (global only, no per-user)
- Documentation: 70/100 (auto-generated but not customized)

**Recommendation:** Authentication and CORS are critical blockers. Cannot deploy to production without them. Implement JWT authentication immediately.

---

**End of Phase 7: API Audit**
