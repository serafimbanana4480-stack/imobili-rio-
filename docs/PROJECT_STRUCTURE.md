# Project Structure

## app/
Core application code.

- `scraping/` — Web scraping spiders and anti-bot systems
- `etl/` — Extract, Transform, Load pipeline
- `valuation/` — Property valuation ML models
- `scoring/` — Opportunity scoring engine
- `dashboard/` — Streamlit analytics dashboard
- `notification/` — Alert and notification system
- `core/` — Business logic and domain models
- `database/` — ORM models and repository pattern
- `scheduler/` — Orchestrator and job scheduling
- `monitoring/` — Health checks and data quality
- `infrastructure/` — Event bus, workers, metrics
- `features/` — Analytics engine and advanced features
- `utils/` — Shared utilities and helpers

## tests/
Comprehensive test suite.

- `unit/` — Isolated component tests
- `integration/` — Cross-component tests
- `e2e/` — End-to-end pipeline tests
- `fixtures/` — Test data and mocks

## scripts/
Automation and utility scripts.

## configs/
Application configuration files.

## data/
Runtime data storage.

- `db/` — SQLite/PostgreSQL databases
- `cache/` — Temporary caches
- `exports/` — Data exports
- `backups/` — Database backups

## docs/
Project documentation.

## docker/
Container definitions.

## ci/
CI/CD pipeline definitions.
