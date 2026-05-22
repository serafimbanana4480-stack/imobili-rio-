# Architecture Overview

## High-Level Flow

```text
Scraping -> ETL -> Geocoding/Enrichment -> Valuation -> Scoring -> Dashboard/Notifications
```

## Core Components

- **Scraping**: Collects listings from real-estate portals using nodriver
- **ETL**: Normalizes and deduplicates listings
- **Database**: Stores raw, clean, valuation, and scoring data (PostgreSQL/SQLite)
- **Valuation Engine**: Estimates fair value using XGBoost with train/test split and model versioning
- **Scoring Engine**: Ranks opportunities by investment quality using weighted scoring
- **Dashboard**: Streamlit interface for operators
- **API**: FastAPI REST API with JWT authentication
- **Monitoring**: Health checks, metrics, and logs
- **Scheduler**: Runs the pipeline on a schedule (APScheduler)
- **Cache**: Redis for query optimization
- **Security**: JWT authentication with bcrypt password hashing, refresh tokens, and rate limiting

## Authentication Flow

```text
User -> Register (bcrypt hash) -> Login (JWT access + refresh tokens) -> API calls (Bearer token)
```

### Authentication Features
- **JWT Access Tokens**: 30 minutes expiration
- **JWT Refresh Tokens**: 7 days expiration
- **Password Hashing**: bcrypt with salt
- **Rate Limiting**: 5 login attempts per minute per IP
- **Token Revocation**: Blacklist for compromised tokens
- **Password Requirements**: 12+ chars, uppercase, lowercase, number, special char

## Database Schema

### Tables
- `raw_listings`: Scraped data from portals
- `clean_listings`: Normalized listings after ETL
- `valuations`: Property valuation estimates
- `scores`: Investment opportunity scores
- `price_history`: Historical price tracking
- `notifications`: Notification history
- `config_entries`: System configuration
- `job_execution_log`: Pipeline execution tracking
- `failed_records`: Failed operations tracking
- `model_versions`: ML model versioning
- `weight_change_audit`: Scoring weight changes audit
- `watchlist`: User watchlist

### Indexes
Optimized indexes for common queries:
- `idx_clean_listings_source_portal`, `idx_clean_listings_freguesia`, `idx_clean_listings_concelho`
- `idx_clean_listings_preco`, `idx_clean_listings_preco_m2`, `idx_clean_listings_area`
- `idx_clean_listings_tipologia`, `idx_clean_listings_estado`, `idx_clean_listings_ano_construcao`
- `idx_clean_listings_agencia`, `idx_clean_listings_is_sample`, `idx_clean_listings_created_at`
- Composite indexes: `idx_clean_listings_concelho_preco`, `idx_clean_listings_freguesia_area`, `idx_clean_listings_portal_estado`

## Caching Strategy

### Redis Cache
- **TTL**: 300 seconds (5 minutes) for most queries
- **Cache Keys**: `clean_listings:<hash>:<limit>:<include_sample>`
- **Fallback**: If Redis unavailable, queries go directly to database
- **Invalidation**: Pattern-based cache clearing on data updates

### Cache Usage
- `get_clean_listings_cached()`: Cached listing queries
- Future: Cache valuations, scores, and aggregations

## ML Model Architecture

### XGBoost Valuation Model
- **Features**: 15+ features including location, condition, energy cert, amenities
- **Training**: Train/test split (80/20) with early stopping
- **Early Stopping**: 50 rounds with validation set
- **Versioning**: Automatic version tracking with timestamp and UUID
- **Persistence**: Saved to disk and database
- **SHAP**: Explainability for predictions

### Model Metrics
- R² score
- Mean Absolute Error (MAE) in log-space
- Best iteration from early stopping
- Feature importance tracking

## API Architecture

### FastAPI Structure
- `api/main.py`: Application entry point
- `api/routers/`: Endpoint modules (auth, listings, valuation, scoring)
- `api/middleware/`: Auth middleware, CORS, rate limiting

### Endpoints
- `/api/v1/auth/`: Authentication (register, login, refresh, verify, logout)
- `/api/v1/listings/`: Listing CRUD operations
- `/api/v1/valuation/`: Property valuation
- `/api/v1/scoring/`: Opportunity scoring
- `/api/v1/health/`: Health checks
- `/docs`: Swagger UI documentation
- `/redoc`: ReDoc documentation

## Performance Optimizations

### Database Connection Pooling
- **pool_size**: 10 (configurable via DB_POOL_SIZE)
- **max_overflow**: 20 (configurable via DB_MAX_OVERFLOW)
- **pool_recycle**: 3600 seconds (configurable via DB_POOL_RECYCLE)
- **pool_pre_ping**: Verify connections before using

### Query Optimization
- Joined eager loading to avoid N+1 queries
- Composite indexes for common filter combinations
- Unique() to prevent duplicate results with joinedload
- Limit and offset for pagination

### Caching
- Redis for frequent queries
- TTL-based expiration
- Pattern-based invalidation

## Security Architecture

### Secrets Management
- **Environment Variables**: All secrets from environment
- **Encryption**: Fernet encryption for sensitive data
- **Validation**: Secret strength validation
- **No Hardcoded Secrets**: Fail loudly if secrets missing

### Security Features
- JWT authentication
- Bcrypt password hashing
- Rate limiting
- CORS configuration
- SQL injection prevention (parameterized queries)
- Input validation (Pydantic models)

## Runtime Directories

- `data/`: persistent data, exports, and backups
- `logs/`: runtime logs and archived outputs
- `scripts/`: operational scripts and launchers
- `tests/`: automated tests and validation checks
- `docs/`: user and technical documentation

## Deployment Architecture

### Docker Compose Services
- `postgres`: PostgreSQL 15 with health checks
- `redis`: Redis 7 with persistence
- `api`: FastAPI application
- `scheduler`: APScheduler for pipeline execution
- `dashboard`: Streamlit UI

### Scaling
- Horizontal scaling via Docker Compose scale command
- Load balancing (nginx recommended for production)
- Database connection pooling for high concurrency

## Monitoring

### Health Checks
- `/api/v1/health/`: Basic health check
- `/api/v1/health/detailed`: Detailed system status

### Metrics
- Prometheus metrics on configurable port (default: 8000)
- Custom metrics for pipeline execution times
- Database query performance tracking

### Logging
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation and archival

## Notes

The repository has been cleaned to keep temporary scripts and reports out of the root directory. This improves maintenance and makes the project easier to hand over to a client.

All authentication, caching, and performance optimizations follow production best practices with proper error handling, logging, and monitoring.
