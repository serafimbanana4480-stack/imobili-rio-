# API Documentation

## Base URL
- Local: `http://localhost:8000`
- Production: `https://api.realestate-engine.com`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. All endpoints except `/api/v1/auth/login` and `/api/v1/auth/register` require a valid access token.

### Obtaining Tokens

#### Register (create account)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Refresh Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

#### Using the Token
Include the access token in the Authorization header:
```bash
curl -H "Authorization: Bearer <access_token>" \
  "http://localhost:8000/api/v1/listings/"
```

### Password Requirements
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*(),.?":{}|<>)

## Main Endpoints

### Health
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system status

### Listings
- `GET /api/v1/listings/` - List all listings (paginated)
- `GET /api/v1/listings/{listing_id}` - Get specific listing

### Valuation
- `POST /api/v1/valuation/` - Valuate a property
- `POST /api/v1/valuation/{listing_id}` - Valuate specific listing

### Scoring
- `POST /api/v1/scoring/` - Score a property
- `POST /api/v1/scoring/{listing_id}` - Score specific listing

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Authenticate and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify` - Verify token validity
- `POST /api/v1/auth/logout` - Logout (revoke token)

## Rate Limiting
- Login: 5 attempts per minute per IP
- API requests: 100 per minute per token

## OpenAPI Documentation
Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables
Required for authentication:
- `JWT_SECRET_KEY` - Secret key for signing JWT tokens
- `JWT_REFRESH_SECRET_KEY` - Secret key for signing refresh tokens
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiration (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (default: 7)
- ReDoc is available at `/redoc`
- The current deployment is intended for internal use
