# API Documentation

## Base URL
- Local: `http://localhost:8000`

## Main Endpoints

### Health
- `GET /api/v1/health/`
- `GET /api/v1/health/detailed`

### Listings
- `GET /api/v1/listings/`
- `GET /api/v1/listings/{listing_id}`

### Valuation
- `POST /api/v1/valuation/`
- `POST /api/v1/valuation/{listing_id}`

### Scoring
- `POST /api/v1/scoring/`
- `POST /api/v1/scoring/{listing_id}`

### Authentication
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/verify`
- `POST /api/v1/auth/logout`

## Notes
- OpenAPI UI is available at `/docs`
- ReDoc is available at `/redoc`
- The current deployment is intended for internal use
