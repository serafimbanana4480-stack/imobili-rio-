# Porto Real Estate Intelligence Engine

## Overview

An autonomous real estate intelligence platform for the Porto metropolitan area that scrapes listings from major portals, evaluates market prices using ML, scores investment opportunities, and presents actionable insights through a professional Streamlit dashboard.

This documentation index now reflects the cleaned repository layout:
- operational scripts live in `scripts/`
- tests live in `tests/`
- long-form reports and validation notes live in `docs/reports/`
- launcher helpers for macOS live in `macos/`
- the human-friendly usage guide lives in `docs/COMO_USAR.md`
- the new quick-use folder lives in `docs/como_usar/`

## System Architecture

```
┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Scrapers   │───▶│    ETL   │───▶│Enrichment│───▶│Valuation │───▶│ Scoring  │
│ (7 portals) │    │ Pipeline │    │ (POI/NLP)│    │  (ML)    │    │ (Score)  │
└─────────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                                          │
                     ┌──────────────────────────────────────────────────┘
                     ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │  Dashboard   │───▶│ Notification │───▶│   Storage    │
            │ (Streamlit)  │    │ (Telegram)   │    │ (SQLite/     │
            └──────────────┘    └──────────────┘    │  PostgreSQL) │
                                                      └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) Docker & Docker Compose

### Installation

```bash
# Clone repository
git clone <repo-url>
cd projeto-analize-mercado-imobiliario

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m realestate_engine.database.models

# Start dashboard
streamlit run realestate_engine/dashboard/app.py

# Run full pipeline (manual)
python -m realestate_engine.scheduler.orchestrator
```

### Docker Compose

```bash
# Start infrastructure
docker compose up -d postgres redis prometheus grafana

# Migrate SQLite → PostgreSQL
python -m realestate_engine.infrastructure.migrate_to_postgres
```

## Project Structure

```
project/
├── realestate_engine/      # Core application code
│   ├── api/                # FastAPI backend
│   ├── dashboard/          # Streamlit analytics UI
│   ├── database/           # ORM models & repository
│   ├── etl/                # Data pipeline
│   ├── monitoring/         # Health checks & metrics
│   ├── scraping/           # Web scraping spiders
│   ├── scoring/            # Opportunity scoring engine
│   ├── valuation/          # ML price estimation models
│   └── utils/              # Shared utilities
├── tests/                  # Test suite
│   ├── unit/               # Component tests
│   ├── integration/        # Cross-layer tests
│   ├── e2e/                # End-to-end pipeline tests
│   └── fixtures/           # Test data
├── scripts/                # Automation and maintenance scripts
├── macos/                  # macOS launcher
├── data/                   # Runtime data
│   ├── db/                 # Databases
│   ├── cache/              # Temporary caches
│   ├── exports/            # Data exports
│   └── backups/            # Backups
├── docs/                   # Documentation
│   └── reports/            # Audit, validation, and sales reports
└── logs/                   # Runtime and archived logs
```

## Key Features

- **Multi-portal scraping:** Idealista, Imovirtual, Casa Sapo, ERA, REMAX, OLX, Century21, SuperCasa
- **Anti-bot evasion:** StealthManager with 2026 fingerprinting techniques
- **ML Valuation:** Weighted ensemble with adaptive weight learning
- **Data Quality:** Real-time drift detection, anomaly alerts, schema validation
- **Investment Dashboard:** Profit potential, ROI calculator, zone rankings
- **Notifications:** Telegram alerts for top opportunities
- **CI/CD:** GitHub Actions with nightly automated tests

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific suite
pytest tests/unit/ -v
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=realestate_engine --cov-report=html
```

## Production Checklist

- [ ] Deploy PostgreSQL + Redis via Docker Compose
- [ ] Migrate SQLite data to PostgreSQL
- [ ] Configure environment variables (`.env`)
- [ ] Set up proxy rotation for scrapers
- [ ] Configure Telegram bot for notifications
- [ ] Enable Grafana dashboards for metrics
- [ ] Schedule daily pipeline runs via Orchestrator
- [ ] Monitor `errors.log` and data quality alerts

## License

Proprietary — Real Estate Intelligence Platform
