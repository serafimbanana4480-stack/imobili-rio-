# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.12
- SSL certificate (for production)

## Local Development

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# Set DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, etc.
```

### 2. Start Services

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using start script (Windows)
start.bat

# Or using start script (Linux/Mac)
./start.sh
```

### 3. Run Tests

```bash
# Activate virtual environment
source venv312/bin/activate  # Linux/Mac
venv312\Scripts\activate  # Windows

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=realestate_engine --cov-report=html
```

## Production Deployment

### 1. Generate Secrets

```bash
# Generate JWT secrets
python -c "import secrets; print(secrets.token_hex(32))"  # JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"  # JWT_REFRESH_SECRET_KEY

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Configure Environment

Create `.env` with production values:

```bash
DATABASE_URL=postgresql://user:password@db-host:5432/realestate
REDIS_URL=redis://redis-host:6379/0
JWT_SECRET_KEY=<your-secret>
JWT_REFRESH_SECRET_KEY=<your-secret>
ENCRYPTION_KEY=<your-key>
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600
```

### 3. Deploy with Docker Compose

```bash
# Build and start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale api=3 --scale scheduler=2
```

### 4. Database Migrations

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Runs security scans (bandit, safety)
2. Runs linters (flake8, black, isort, mypy)
3. Runs tests with coverage
4. Deploys to staging on develop branch
5. Deploys to production on main branch

## Monitoring

### Health Checks

```bash
# API health check
curl http://localhost:8000/api/v1/health/

# Detailed health check
curl http://localhost:8000/api/v1/health/detailed
```

### Metrics

Prometheus metrics are available at:
- `http://localhost:8000/metrics` (default port: 8000)

Configure in `.env`:
```bash
PROMETHEUS_PORT=8000
```

### Logging

Logs are written to:
- Console (structured JSON)
- File: `logs/realestate_engine.log`
- Log level: `LOG_LEVEL=INFO` (or `DEBUG` for development)

## Security Checklist

- [ ] JWT_SECRET_KEY set (32+ characters)
- [ ] JWT_REFRESH_SECRET_KEY set (32+ characters)
- [ ] ENCRYPTION_KEY set
- [ ] DATABASE_PASSWORD is strong
- [ ] SSL/TLS enabled for production
- [ ] Firewall configured
- [ ] Redis password set
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Secrets not committed to git

## Backup Strategy

### Database Backups

```bash
# Backup PostgreSQL
pg_dump -U realestate realestate > backup_$(date +%Y%m%d).sql

# Restore
psql -U realestate realestate < backup_20240101.sql
```

### Model Backups

XGBoost models are automatically versioned and saved to:
- `data/models/xgboost_<version>.pkl`
- Database table `model_versions`

### Redis Backup

```bash
# Save Redis snapshot
redis-cli SAVE

# Copy dump file
cp /var/lib/redis/dump.rdb /backup/
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Redis Connection Issues

```bash
# Check Redis status
redis-cli ping

# View logs
docker-compose logs redis
```

### API Not Responding

```bash
# Check API status
curl http://localhost:8000/api/v1/health/

# View logs
docker-compose logs api

# Restart API
docker-compose restart api
```

### High Memory Usage

1. Reduce `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
2. Reduce `DB_POOL_RECYCLE`
3. Check for memory leaks in logs
4. Monitor with Prometheus/Grafana

## Performance Tuning

### Database

- **pool_size**: 10-20 (based on CPU cores)
- **max_overflow**: 20-40 (for peak loads)
- **pool_recycle**: 3600 (1 hour, prevents stale connections)

### Cache

- Redis TTL: 300 seconds (5 minutes) for most queries
- Adjust based on data freshness requirements

### API

- Workers: 3-5 instances behind load balancer
- Enable Gunicorn/uvicorn workers for production

## Scaling

### Horizontal Scaling

```bash
# Scale API to 3 instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale scheduler to 2 instances
docker-compose -f docker-compose.prod.yml up -d --scale scheduler=2
```

### Vertical Scaling

- Increase CPU cores
- Add more RAM
- Use SSD storage for database

## Maintenance

### Daily

- Monitor logs for errors
- Check disk space
- Verify backups completed

### Weekly

- Review performance metrics
- Check for security updates
- Review failed records table

### Monthly

- Database vacuum/analyze
- Clean old logs
- Review and rotate secrets
- Update dependencies
