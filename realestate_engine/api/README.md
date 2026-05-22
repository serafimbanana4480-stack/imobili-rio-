# Real Estate Engine API

REST API for the Real Estate Opportunity Engine.

## Features

- **Authentication**: Disabled for internal use in the current deployment
- **Rate Limiting**: Configurable rate limits per endpoint
- **OpenAPI Documentation**: Auto-generated Swagger docs at `/docs`
- **CORS Support**: Configurable CORS middleware

## Installation

The API dependencies are already included in `requirements.txt`:
- fastapi>=0.104.0
- uvicorn>=0.24.0
- pyjwt>=2.8.0
- slowapi>=0.1.9

## Running the API

### Development

```bash
# From project root
cd realestate_engine
python -m api.main
```

Or use the startup scripts in `scripts/`:

**Windows:**
```bash
scripts/start_api.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start_api.sh
./scripts/start_api.sh
```

### Production

```bash
uvicorn realestate_engine.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Authentication
- Authentication routes are not included in the internal-use deployment

### Listings
- `GET /api/v1/listings/` - Get paginated listings with filters
- `GET /api/v1/listings/{listing_id}` - Get specific listing

### Valuation
- `POST /api/v1/valuation/` - Valuate property (manual data)
- `POST /api/v1/valuation/{listing_id}` - Valuate listing from database

### Scoring
- `POST /api/v1/scoring/` - Score property (manual data)
- `POST /api/v1/scoring/{listing_id}` - Score listing from database

### Health
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check with component status

## Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

The current deployment is intended for internal use, so the auth router is disabled. If you later need public access, re-enable the router and add production authentication.

## Rate Limits

Default rate limits:
- Listings: 200/hour
- Valuation: 20/hour
- Scoring: 30/hour
- Default: 100/hour

Configure in `api/middleware/rate_limit.py`

## Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///data/db/realestate.db

# API
DEV_MODE=true  # Internal-use deployment only
JWT_SECRET_KEY=your-secret-key-change-in-production

# Logging
LOG_LEVEL=INFO
```

## Example Usage

### 1. Login and get token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

### 2. Get listings (no auth required in dev mode)
```bash
curl http://localhost:8000/api/v1/listings/?page=1&page_size=10
```

### 3. Valuate a property
```bash
curl -X POST http://localhost:8000/api/v1/valuation/ \
  -H "Content-Type: application/json" \
  -d '{
    "preco_pedido": 250000,
    "area_util_m2": 80,
    "quartos": 2,
    "casas_banho": 1,
    "concelho": "Porto",
    "freguesia": "Bonfim"
  }'
```

### 4. Score a property
```bash
curl -X POST http://localhost:8000/api/v1/scoring/ \
  -H "Content-Type: application/json" \
  -d '{
    "preco_pedido": 250000,
    "area_util_m2": 80,
    "quartos": 2,
    "concelho": "Porto"
  }'
```

## Development Notes

- The API uses dependency injection for database repository and engines
- Rate limiting is implemented using slowapi
- JWT authentication uses PyJWT
- CORS is enabled for all origins in development (configure for production)
- OpenAPI documentation is auto-generated from Pydantic schemas
