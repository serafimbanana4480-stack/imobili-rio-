# Real Estate AI Platform - Sale Documentation

Complete documentation for buyers of the Real Estate Intelligence Engine platform.

## Table of Contents
1. [System Overview](#system-overview)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Configuration Guide](#configuration-guide)
5. [User Manual](#user-manual)
6. [API Documentation](#api-documentation)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Support Information](#support-information)

---

## System Overview

The Real Estate Intelligence Engine is a comprehensive platform for automated property valuation, scoring, and opportunity detection in the Portuguese real estate market.

### Key Features
- **Automated Scraping**: Scrapes listings from major Portuguese real estate portals (Casa Sapo)
- **AI-Powered Valuation**: Multi-model valuation engine using hedonic pricing and INE data
- **Opportunity Scoring**: Multi-factor scoring algorithm to identify investment opportunities
- **Interactive Dashboard**: Streamlit-based dashboard for data visualization and analysis
- **REST API**: Complete API for integration with other systems
- **Real-time Monitoring**: Health checks, metrics collection, and alerting

### Architecture
- **Backend**: Python 3.12+ with FastAPI
- **Database**: SQLite (production-ready, can be upgraded to PostgreSQL)
- **Frontend**: Streamlit dashboard
- **AI/ML**: Custom valuation and scoring engines
- **Monitoring**: Prometheus metrics and health checks

---

## System Requirements

### Hardware Requirements
- **CPU**: 4 cores or higher recommended
- **RAM**: 8GB minimum, 16GB recommended for large datasets
- **Disk**: 20GB minimum SSD storage
- **Network**: Stable internet connection for scraping and API access

### Software Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS 10.15+
- **Python**: 3.12 or higher
- **Git**: For cloning the repository

### Optional Requirements
- **Ollama**: For AI-powered deal analysis (local LLM)
- **Telegram Bot**: For notification alerts
- **Cloudflare Account**: For free HTTPS tunnel (optional)

---

## Installation Guide

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv312
venv312\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv312
source venv312/bin/activate
```

### Step 3: Install Dependencies

```bash
cd realestate_engine
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration (see [Configuration Guide](#configuration-guide))

### Step 5: Initialize Database

```bash
python -c "from realestate_engine.database.models import init_db; from realestate_engine.utils.config import config; init_db(config.database_url)"
```

### Step 6: Start the Services

**Option A: Start All Services**
```bash
start_all.bat
```

**Option B: Start the 24H engine**
```bash
start_engine_24h.bat
```

**Option C: Start dashboard + API**
```bash
start_dashboard_backend.bat
```

**Option D: Start everything**
```bash
start_all.bat
```

**Option E: Start Manually**

Start API server:
```bash
cd realestate_engine
python -m api.main
```

Start dashboard (in separate terminal):
```bash
cd realestate_engine/dashboard
streamlit run app.py
```

### Step 7: Verify Installation

Open your browser and navigate to:
- Dashboard: http://localhost:8501
- API Health: http://localhost:8000/api/v1/health/
- API Documentation: http://localhost:8000/docs

---

## Configuration Guide

### Environment Variables

Edit the `.env` file in the project root:

#### Database Configuration
```env
# SQLite (default, recommended for most users)
DATABASE_URL=sqlite:///data/db/realestate.db

# PostgreSQL (for enterprise deployments)
# DATABASE_URL=postgresql://user:password@localhost:5432/realestate
```

#### Telegram Notifications (Optional)
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Get your bot token from [@BotFather](https://t.me/botfather) and chat ID from [@userinfobot](https://t.me/userinfobot).

#### Scraping Configuration
```env
# Residential proxy (required for some portals)
RESIDENTIAL_PROXY_URL=http://user:password@proxy-host:port

# Scraping intervals (minutes)
SCRAPING_INTERVAL_MINUTES=30
ETL_INTERVAL_MINUTES=32
VALUATION_INTERVAL_MINUTES=35
SCORING_INTERVAL_MINUTES=38
```

#### Geocoding Configuration
```env
# Google Geocoding API (optional, for better accuracy)
GOOGLE_GEOCODING_API_KEY=your_api_key

# Nominatim (free, default)
# No configuration needed
```

#### AI Configuration (Optional)
```env
# Ollama for AI deal analysis
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

#### Logging Configuration
```env
LOG_LEVEL=INFO
```

### Dashboard Configuration

Access the dashboard and navigate to **Configuração** to set:
- Active regions (concelhos)
- Price ranges
- Minimum score for notifications
- Scoring weights
- Telegram credentials
- Ollama model settings

---

## User Manual

### Dashboard Overview

The dashboard provides an intuitive interface for:

1. **Overview (Página Inicial)**: Quick summary of opportunities and market insights
2. **Pesquisa & Filtros**: Search and filter listings
3. **Análise de Mercado**: Market trends and statistics
4. **Ferramentas de Investidor**: ROI calculators and investment tools
5. **Análise IA**: AI-powered deal analysis (requires Ollama)
6. **Telegram**: Configure notification alerts
7. **Configuração**: System settings and preferences
8. **Sistema**: System health and status
9. **Resultados de Scraping**: Scraping results and logs
10. **Pipeline Status**: ETL pipeline status
11. **Watchlist**: Save and track interesting properties
12. **Mapa**: Geographic visualization of listings
13. **Qualidade de Dados**: Data quality metrics
14. **Debug & Logs**: System logs and debugging tools

### Common Workflows

#### Finding Investment Opportunities
1. Navigate to **Pesquisa & Filtros**
2. Set your criteria (price, location, property type)
3. Click **🔍 Pesquisar**
4. Sort by score to find best opportunities
5. Click **⭐ Add to Watchlist** for interesting properties

#### Running a Full Pipeline
1. Navigate to **Sistema**
2. Click **▶️ Executar Scraping** to scrape new listings
3. Click **🔄 Pipeline Completo** to run ETL, valuation, and scoring
4. Monitor progress in **Pipeline Status**

#### Analyzing a Property
1. Navigate to **Pesquisa & Filtros**
2. Find a property of interest
3. View valuation details (estimated price, confidence interval)
4. View scoring breakdown (discount, location, condition, amenities)
5. Use **Ferramentas de Investidor** for ROI calculations

#### Setting Up Notifications
1. Navigate to **Telegram**
2. Enter your Telegram bot token and chat ID
3. Click **💾 Guardar Credenciais**
4. Click **📡 Detetar Chat ID** to verify
5. Click **📤 Enviar Mensagem de Teste** to test notifications

---

## API Documentation

### Base URL
- HTTP: `http://localhost:8000`
- HTTPS: `https://your-domain.com` (with Cloudflare Tunnel)

### Authentication
The system is designed for internal use and does not require authentication. All endpoints are publicly accessible within your network.

### Endpoints

#### Health Check
```http
GET /api/v1/health/
```

Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Real Estate Engine API",
  "version": "1.0.0"
}
```

#### Detailed Health Check
```http
GET /api/v1/health/detailed
```

Returns detailed health status of all components.

**Response:**
```json
{
  "status": "healthy",
  "service": "Real Estate Engine API",
  "version": "1.0.0",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "valuation_engine": "healthy",
    "scoring_engine": "healthy"
  }
}
```

#### Get Listings
```http
GET /api/v1/listings/?page=1&page_size=10
```

Query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)
- `concelho`: Filter by municipality
- `min_score`: Filter by minimum score
- `max_price`: Filter by maximum price

**Response:**
```json
{
  "listings": [...],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

#### Valuation
```http
POST /api/v1/valuation/
```

Request body:
```json
{
  "preco_pedido": 250000,
  "area_util_m2": 80,
  "quartos": 2,
  "casas_banho": 1,
  "concelho": "Porto",
  "freguesia": "Bonfim"
}
```

**Response:**
```json
{
  "valor_justo": 182677.11,
  "ci_lower": 147154.88,
  "ci_upper": 264939.12,
  "confianca": 0.64,
  "discount": -0.3685,
  "hedonic_value": 176000.0,
  "ine_value": 236094.0,
  "ensemble_weights": {
    "hedonic": 0.89,
    "ine": 0.11
  },
  "market_context": {
    "median_price_m2": 2850.0,
    "yoy_variation_pct": 14.2,
    "monthly_trend_pct": 1.18
  }
}
```

#### Scoring
```http
POST /api/v1/scoring/
```

Request body:
```json
{
  "preco_pedido": 250000,
  "area_util_m2": 80,
  "quartos": 2,
  "casas_banho": 1,
  "concelho": "Porto"
}
```

**Response:**
```json
{
  "score_total": 7.5,
  "classificacao": "Excelente oportunidade",
  "score_discount": 8.0,
  "score_location": 7.5,
  "score_condition": 6.0,
  "score_amenities": 7.0,
  "score_liquidity": 8.0,
  "score_freshness": 7.5,
  "rationale": "Detailed analysis...",
  "red_flags": ["Flag1", "Flag2"],
  "has_critical_flags": false
}
```

### Interactive API Documentation
Navigate to `http://localhost:8000/docs` for interactive API documentation with Swagger UI.

---

## Troubleshooting Guide

### Common Issues

#### API Won't Start
**Problem**: API server fails to start
**Solution**:
1. Check if port 8000 is already in use
2. Verify database URL in `.env` is correct
3. Check Python dependencies are installed
4. Review logs in `logs/api.log`

#### Dashboard Won't Start
**Problem**: Streamlit dashboard fails to start
**Solution**:
1. Check if port 8501 is already in use
2. Verify Streamlit is installed: `pip install streamlit`
3. Check Python version (requires 3.12+)
4. Review logs in `logs/dashboard.log`

#### Scraping Fails
**Problem**: Web scraping returns no results or errors
**Solution**:
1. Check if target portal is accessible
2. Verify proxy configuration if required
3. Check internet connection
4. Review logs in `logs/scraping.log`
5. Some portals may block scraping - this is expected

#### Database Errors
**Problem**: Database connection or query errors
**Solution**:
1. Verify database file exists and is writable
2. Check database URL in `.env`
3. Ensure sufficient disk space
4. Try deleting and recreating database (WARNING: loses data)

#### Out of Memory
**Problem**: System runs out of memory with large datasets
**Solution**:
1. Increase system RAM
2. Process data in smaller batches
3. Close unused applications
4. Consider using PostgreSQL for better memory management

### Log Files

All logs are stored in the `logs/` directory:
- `api.log`: API server logs
- `dashboard.log`: Dashboard logs
- `scraping.log`: Web scraping logs
- `etl.log`: ETL pipeline logs
- `valuation.log`: Valuation engine logs
- `scoring.log`: Scoring engine logs
- `errors.log`: Error logs (all components)

### Getting Help

If you encounter issues not covered in this guide:
1. Check the error logs for detailed information
2. Review the GitHub issues page
3. Contact support (see [Support Information](#support-information))

---

## Support Information

### Support Channels

**Email**: support@your-domain.com
**Telegram**: @your-support-bot
**Response Time**: 24-48 hours

### Support Scope

Included in your subscription:
- Installation assistance
- Configuration help
- Bug fixes and updates
- Feature requests (considered for future releases)

Not included:
- Custom development
- Data entry services
- Third-party integrations
- Training beyond this documentation

### Version Updates

The platform receives regular updates including:
- Bug fixes
- Performance improvements
- New features
- Security patches

Updates are delivered via:
- Git repository updates
- Automated upgrade scripts (when available)
- Manual installation instructions

### Backup Recommendations

Regular backups are recommended:
1. **Database Backup**: Backup `data/db/realestate.db` weekly
2. **Configuration Backup**: Backup `.env` file
3. **Code Backup**: Keep a copy of the repository

### Security Recommendations

1. **Network Security**: Run behind a firewall
2. **HTTPS**: Use Cloudflare Tunnel or similar for HTTPS
3. **Access Control**: Limit network access to trusted users
4. **Updates**: Keep Python and dependencies updated
5. **Monitoring**: Monitor logs for suspicious activity

---

## Appendix

### Glossary

- **ETL**: Extract, Transform, Load - data pipeline process
- **INE**: Instituto Nacional de Estatística (Portuguese statistics bureau)
- **ROI**: Return on Investment
- **API**: Application Programming Interface
- **Dashboard**: Visual interface for data visualization

### Third-Party Services

The platform integrates with:
- **Casa Sapo**: Real estate portal (scraping)
- **INE**: Portuguese statistics bureau (market data)
- **Nominatim**: OpenStreetMap geocoding service
- **Ollama**: Local LLM for AI analysis (optional)
- **Telegram**: Notification service (optional)
- **Cloudflare**: HTTPS tunnel service (optional)

### License Information

This software is sold under a commercial license. See your license agreement for details on:
- Permitted usage
- Number of installations
- Support terms
- Update policy

---

**Document Version**: 1.0  
**Last Updated**: April 2026  
**Platform Version**: 1.0.0
