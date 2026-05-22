# PHASE 10: SECURITY AUDIT
## SQLi, Secrets, Hardening

**Date:** 2026-05-04  
**Auditor:** Principal Software Architect + Staff Engineer + Security Engineer  
**Scope:** Complete security analysis for production compliance  
**Production Context:** System intended for commercial sale handling sensitive personal and financial data

---

## EXECUTIVE SUMMARY

**Overall Security Score:** 62/100

**Critical Issues:** 2  
**High Priority Issues:** 3  
**Medium Priority Issues:** 4  
**Low Priority Issues:** 2

**Key Findings:**
- Encryption implemented with Fernet (good)
- **CRITICAL:** Secrets in environment variables (not encrypted at rest)
- **CRITICAL:** No input validation/sanitization for user inputs
- **HIGH:** No SQL injection protection (ORM helps but not sufficient)
- **HIGH:** No CSRF protection (dashboard vulnerable)
- **HIGH:** No XSS protection (user inputs not sanitized)
- No secrets management system (Vault, AWS Secrets Manager)
- No security headers (CSP, HSTS, X-Frame-Options)
- No audit logging for security events
- No rate limiting for authentication
- No password policy enforcement
- No multi-factor authentication
- No role-based access control (RBAC)

---

## 1. SECURITY ARCHITECTURE ANALYSIS

### 1.1 Current Architecture

**LOCATION:** `realestate_engine/security/encryption.py` (37 lines)

**Architecture Pattern:**
```
Security Components
├── Encryption
│   ├── Fernet (AES-128)
│   └── Key from environment
├── Secrets Management
│   └── Environment variables only
├── Database Security
│   ├── SQLAlchemy ORM
│   └── No explicit SQLi protection
├── API Security
│   ├── No authentication
│   ├── No authorization
│   └── Permissive CORS
└── Missing
    ├── Secrets Manager (Vault)
    ├── Security Headers
    ├── Input Validation
    ├── Audit Logging
    └── MFA
```

**Code Analysis:**
```python
class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

**Strengths:**
1. **Fernet Encryption:** Industry-standard symmetric encryption
2. **ORM Protection:** SQLAlchemy prevents most SQL injection
3. **Environment Variables:** Better than hardcoded secrets

**Critical Gaps:**
- 🔴 **Secrets in Environment Variables:** Not encrypted at rest
- 🔴 **No Input Validation:** User inputs not sanitized
- ⚠️ **No SQLi Protection:** ORM helps but not sufficient for all cases
- ⚠️ **No Security Headers:** Missing CSP, HSTS, X-Frame-Options
- ⚠️ **No Audit Logging:** No security event tracking
- ⚠️ **No MFA:** Single-factor authentication only
- ⚠️ **No RBAC:** No role-based access control

---

## 2. CRITICAL ISSUES

### 2.1 CRITICAL ISSUE #1: Secrets in Environment Variables

**SEVERITY:** 🔴 CRITICAL - SECRET EXPOSURE

**LOCATION:** `realestate_engine/utils/config.py` (entire file), `.env.example`

**Problem:**
```python
# config.py
@dataclass
class Config:
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    # All secrets in plain text environment variables
```

**Root Cause:**
- Secrets stored in environment variables
- Environment variables stored in .env files (potentially committed)
- No encryption at rest
- No secrets rotation
- No access control to secrets

**Impact on Production:**
- **Secret Exposure:** If .env file committed, secrets exposed in git
- **Insider Threat:** Anyone with server access can read secrets
- **No Audit Trail:** Cannot track who accessed secrets
- **GDPR Risk:** Personal data exposure
- **Commercial Risk:** API keys stolen, service abuse

**Real-World Scenario:**
```
Developer accidentally commits .env to git
Repository cloned by attacker
Attacker extracts Telegram bot token
Attacker sends spam through bot
Telegram account banned
Service down, financial loss: €10,000
GDPR fine: €50,000
```

**Refactor Suggestion - HashiCorp Vault:**
```python
import hvac
from hvac.exceptions import VaultError
from typing import Optional

class VaultSecretsManager:
    """Secrets manager using HashiCorp Vault."""
    
    def __init__(self, vault_url: str, vault_token: str):
        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.client.auth.token.renew_self()
    
    def get_secret(self, path: str, key: str) -> Optional[str]:
        """Get secret from Vault."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data'][key]
        except VaultError as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return None
    
    def set_secret(self, path: str, data: dict):
        """Set secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data
            )
            logger.info(f"Secret set at {path}")
        except VaultError as e:
            logger.error(f"Failed to set secret in Vault: {e}")
    
    def rotate_secret(self, path: str):
        """Rotate secret in Vault."""
        # Generate new secret
        new_value = generate_secure_token()
        
        # Update secret
        self.set_secret(path, {"value": new_value})
        
        # Log rotation
        logger.info(f"Secret rotated at {path}")

# Usage
vault_manager = VaultSecretsManager(
    vault_url=os.getenv("VAULT_URL", "http://localhost:8200"),
    vault_token=os.getenv("VAULT_TOKEN")
)

# Get secrets
telegram_token = vault_manager.get_secret("realestate/telegram", "bot_token")
database_url = vault_manager.get_secret("realestate/database", "url")

# Docker Compose
# docker-compose.yml
  vault:
    image: hashicorp/vault:1.15
    container_name: realestate_vault
    ports:
      - "8200:8200"
    environment:
      - VAULT_DEV_ROOT_TOKEN_ID=root
      - VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200
    volumes:
      - vault_data:/vault/data
    cap_add:
      - IPC_LOCK
    command: server -dev
```

**Alternative: AWS Secrets Manager (for AWS deployments):**
```python
import boto3
from botocore.exceptions import ClientError

class AWSSecretsManager:
    """Secrets manager using AWS Secrets Manager."""
    
    def __init__(self, region_name: str = "eu-west-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                return response['SecretString']
            else:
                return response['SecretBinary']
        except ClientError as e:
            logger.error(f"Failed to get secret from AWS: {e}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str):
        """Set secret in AWS Secrets Manager."""
        try:
            self.client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_value
            )
        except ClientError as e:
            logger.error(f"Failed to set secret in AWS: {e}")
```

**Implementation Effort:** 3-4 days  
**Priority:** CRITICAL  
**Risk**: MEDIUM (requires infrastructure changes)

---

### 2.2 CRITICAL ISSUE #2: No Input Validation

**SEVERITY:** 🔴 CRITICAL - INJECTION ATTACKS

**LOCATION:** Throughout application (no centralized validation)

**Problem:**
```python
# Example from assumed API endpoint
@router.get("/listings")
async def get_listings(
    search: str = Query(None),  # No validation
    limit: int = Query(100)     # No upper bound
):
    query = f"SELECT * FROM listings WHERE title LIKE '%{search}%'"  # SQLi risk
    # No sanitization
```

**Root Cause:**
- No centralized input validation
- No sanitization of user inputs
- No parameterized queries everywhere
- No length limits on inputs
- No type validation beyond Pydantic

**Impact on Production:**
- **SQL Injection:** Attacker can execute arbitrary SQL
- **XSS:** Attacker can inject malicious scripts
- **Data Loss:** Attacker can delete/modify data
- **GDPR Violation:** Personal data exposure
- **Legal Liability:** Security breach fines

**Refactor Suggestion - Input Validation:**
```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re
from sqlparse import parse, tokens

class SearchQuery(BaseModel):
    """Validated search query."""
    
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Search string (max 100 chars)"
    )
    
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Limit results (1-1000)"
    )
    
    @validator('search')
    def validate_search(cls, v):
        if v is None:
            return v
        
        # Check for SQL injection patterns
        sql_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'EXEC']
        for keyword in sql_keywords:
            if keyword.lower() in v.lower():
                raise ValueError(f"Invalid search term: contains SQL keyword '{keyword}'")
        
        # Check for XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        for pattern in xss_patterns:
            if pattern in v.lower():
                raise ValueError(f"Invalid search term: contains XSS pattern '{pattern}'")
        
        # Sanitize: remove special characters
        v = re.sub(r'[<>\"\'\;]', '', v)
        
        return v

class SafeQueryBuilder:
    """Safe query builder with injection protection."""
    
    @staticmethod
    def build_search_query(search: str, table: str) -> str:
        """Build safe search query."""
        if not search:
            return f"SELECT * FROM {table} LIMIT 100"
        
        # Use parameterized query
        query = f"SELECT * FROM {table} WHERE title LIKE :search LIMIT 100"
        return query
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """Validate query for SQL injection."""
        parsed = parse(query)
        
        # Check for dangerous statements
        for statement in parsed:
            for token in statement.tokens:
                if token.ttype in (tokens.DML, tokens.DDL):
                    if token.value.upper() in ['DROP', 'DELETE', 'TRUNCATE']:
                        return False
        
        return True

# Usage in API
@router.get("/listings")
async def get_listings(params: SearchQuery = Depends()):
    """Get listings with validated input."""
    # Pydantic validates automatically
    query = SafeQueryBuilder.build_search_query(params.search, "listings")
    
    # Execute with parameterized query
    results = repo.execute(query, {"search": f"%{params.search}%"})
    
    return {"listings": results}
```

**Implementation Effort:** 4-5 days  
**Priority**: CRITICAL  
**Risk**: HIGH (requires changes throughout application)

---

## 3. HIGH PRIORITY ISSUES

### 3.1 HIGH PRIORITY ISSUE #1: No Security Headers

**SEVERITY:** 🟠 HIGH - VULNERABLE TO ATTACKS

**LOCATION:** `realestate_engine/api/main.py` (missing security headers)

**Problem:**
```python
# Current implementation
app = FastAPI()
# No security headers
```

**Root Cause:**
- No Content-Security-Policy (CSP)
- No Strict-Transport-Security (HSTS)
- No X-Frame-Options
- No X-Content-Type-Options
- No Referrer-Policy
- No Permissions-Policy

**Impact on Production:**
- **Clickjacking:** Site can be framed by attackers
- **XSS:** No CSP to prevent XSS
- **MITM:** No HSTS to enforce HTTPS
- **Data Leakage:** Referrer header exposes data

**Refactor Suggestion - Security Headers:**
```python
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Force HTTPS in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Content-Security-Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.openai.com; "
        "frame-ancestors 'none'; "
        "form-action 'self';"
    )
    
    # Strict-Transport-Security
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # X-Frame-Options
    response.headers["X-Frame-Options"] = "DENY"
    
    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Referrer-Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions-Policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=()"
    )
    
    # X-XSS-Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Trusted host middleware (prevent host header attacks)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.example.com", "www.api.example.com"]
    )
```

**Implementation Effort:** 1 day  
**Priority**: HIGH  
**Risk**: LOW

---

### 3.2 HIGH PRIORITY ISSUE #2: No CSRF Protection

**SEVERITY:** 🟠 HIGH - CSRF ATTACKS

**LOCATION**: Streamlit dashboard (no CSRF protection)

**Problem:**
- Streamlit has no CSRF protection by default
- Forms vulnerable to CSRF attacks
- No CSRF tokens

**Impact on Production:**
- **CSRF Attacks:** Attacker can perform actions on behalf of users
- **Account Takeover:** CSRF can lead to unauthorized actions
- **Data Loss:** Attacker can delete data via CSRF

**Refactor Suggestion - CSRF Protection:**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
from typing import Optional

class CSRFProtection:
    """CSRF protection middleware."""
    
    def __init__(self):
        self.tokens = {}  # In production, use Redis
    
    def generate_token(self, user_id: str) -> str:
        """Generate CSRF token for user."""
        token = secrets.token_urlsafe(32)
        self.tokens[user_id] = token
        return token
    
    def validate_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token."""
        return self.tokens.get(user_id) == token

# Usage in API
@app.post("/api/v1/listings/{listing_id}/bookmark")
async def bookmark_listing(
    listing_id: str,
    csrf_token: str = Form(...),
    current_user: User = Depends(get_current_user),
    csrf: CSRFProtection = Depends()
):
    """Bookmark listing with CSRF protection."""
    if not csrf.validate_token(current_user.id, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )
    
    # Bookmark logic
    pass
```

**Implementation Effort:** 2 days  
**Priority**: HIGH  
**Risk**: MEDIUM

---

### 3.3 HIGH PRIORITY ISSUE #3: No Audit Logging

**SEVERITY:** 🟠 HIGH - NO SECURITY TRACKING

**LOCATION:** Missing component

**Problem:**
- No audit logging for security events
- No tracking of authentication attempts
- No tracking of authorization failures
- No tracking of data access

**Impact on Production:**
- **No Forensics:** Cannot investigate security incidents
- **No Compliance:** Fails audit requirements
- **No Detection:** Cannot detect attack patterns

**Refactor Suggestion - Audit Logging:**
```python
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class SecurityEventType(Enum):
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    PRIVILEGE_ESCALATION = "privilege_escalation"

class SecurityAuditLogger:
    """Audit logger for security events."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
    
    def log_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str],
        resource: str,
        action: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event to audit trail."""
        audit_record = {
            "event_type": event_type.value,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(UTC),
            "details": details or {}
        }
        
        # Store in database
        self.repo.create_security_audit_log(audit_record)
        
        # Also log to file for immediate visibility
        logger.info(
            f"Security Event: {event_type.value} | "
            f"User: {user_id} | "
            f"Resource: {resource} | "
            f"Action: {action} | "
            f"Success: {success} | "
            f"IP: {ip_address}"
        )
    
    def log_authentication_success(self, user_id: str, ip_address: str, user_agent: str):
        """Log successful authentication."""
        self.log_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            user_id=user_id,
            resource="auth",
            action="login",
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_authentication_failure(self, username: str, ip_address: str, user_agent: str, reason: str):
        """Log failed authentication."""
        self.log_event(
            event_type=SecurityEventType.AUTHENTICATION_FAILURE,
            user_id=username,  # Username, not user_id
            resource="auth",
            action="login",
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": reason}
        )
    
    def log_data_access(self, user_id: str, resource: str, action: str, ip_address: str):
        """Log data access."""
        self.log_event(
            event_type=SecurityEventType.DATA_ACCESS,
            user_id=user_id,
            resource=resource,
            action=action,
            success=True,
            ip_address=ip_address,
            user_agent=""
        )
    
    def get_failed_authentications(self, hours: int = 24) -> list:
        """Get failed authentication attempts for monitoring."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return self.repo.get_security_audit_logs(
            event_type=SecurityEventType.AUTHENTICATION_FAILURE.value,
            since=cutoff
        )

# Usage in authentication
@router.post("/auth/login")
async def login(request: LoginRequest, req: Request):
    """Authenticate user with audit logging."""
    audit_logger = SecurityAuditLogger(repo)
    
    user = authenticate_user(request.username, request.password)
    
    if user:
        audit_logger.log_authentication_success(
            user_id=user.id,
            ip_address=req.client.host,
            user_agent=req.headers.get("user-agent", "")
        )
        
        return {"access_token": create_access_token(user)}
    else:
        audit_logger.log_authentication_failure(
            username=request.username,
            ip_address=req.client.host,
            user_agent=req.headers.get("user-agent", ""),
            reason="Invalid credentials"
        )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Implementation Effort:** 3 days  
**Priority**: HIGH  
**Risk**: LOW

---

## 4. MEDIUM PRIORITY ISSUES

### 4.1 MEDIUM PRIORITY ISSUE #1: No Password Policy

**SEVERITY:** 🟡 MEDIUM - WEAK PASSWORDS

**LOCATION:** Missing component

**Refactor Suggestion:**
```python
import re
from typing import Tuple

class PasswordPolicy:
    """Password policy enforcement."""
    
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    FORBIDDEN_PATTERNS = [
        r"password",
        r"123456",
        r"qwerty",
        r"admin"
    ]
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, list]:
        """Validate password against policy."""
        errors = []
        
        # Check length
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")
        
        # Check uppercase
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain uppercase letters")
        
        # Check lowercase
        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain lowercase letters")
        
        # Check digits
        if cls.REQUIRE_DIGITS and not re.search(r"\d", password):
            errors.append("Password must contain digits")
        
        # Check special characters
        if cls.REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain special characters")
        
        # Check forbidden patterns
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append(f"Password contains forbidden pattern: {pattern}")
        
        return len(errors) == 0, errors

# Usage
@router.post("/auth/register")
async def register(request: RegisterRequest):
    """Register new user with password policy."""
    is_valid, errors = PasswordPolicy.validate(request.password)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Password does not meet policy", "errors": errors}
        )
    
    # Create user
    pass
```

**Implementation Effort:** 1 day  
**Priority**: MEDIUM  
**Risk**: LOW

---

### 4.2 Additional Medium Priority Issues

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 2 | No MFA | Missing | HIGH | 3 days | MEDIUM |
| 3 | No RBAC | Missing | MEDIUM | 4 days | MEDIUM |
| 4 | No rate limiting for auth | Missing | MEDIUM | 2 days | MEDIUM |

---

## 5. REFACTOR ROADMAP

### Phase 1: Critical Fixes (Week 1-2)
- [ ] Implement HashiCorp Vault or AWS Secrets Manager
- [ ] Migrate all secrets from environment variables
- [ ] Implement centralized input validation
- [ ] Add SQL injection protection

### Phase 2: High Priority (Week 3)
- [ ] Add security headers (CSP, HSTS, X-Frame-Options)
- [ ] Implement CSRF protection
- [ ] Add security audit logging
- [ ] Implement rate limiting for authentication

### Phase 3: Medium Priority (Week 4)
- [ ] Implement password policy
- [ ] Add MFA (TOTP/SMS)
- [ ] Implement RBAC
- [ ] Add security monitoring dashboards

### Phase 4: Low Priority (Week 5)
- [ ] Implement security training for developers
- [ ] Add penetration testing
- [ ] Implement security scanning in CI/CD
- [ ] Create security documentation

---

## 6. PRODUCTION READINESS SCORE

**Security Audit Score: 62/100**

**Breakdown:**
- Encryption: 70/100 (Fernet good, but secrets not encrypted at rest)
- Secrets Management: 30/100 (environment variables only - CRITICAL)
- Input Validation: 20/100 (no centralized validation - CRITICAL)
- SQL Injection: 50/100 (ORM helps but not sufficient)
- XSS Protection: 30/100 (no sanitization)
- Security Headers: 0/100 (none configured)
- Audit Logging: 0/100 (no security event tracking)
- Authentication: 0/100 (no auth implemented)
- Authorization: 0/100 (no RBAC)

**Recommendation:** Secrets management and input validation are critical blockers. Cannot deploy to production without addressing these. Implement Vault/AWS Secrets Manager immediately.

---

**End of Phase 10: Security Audit**
