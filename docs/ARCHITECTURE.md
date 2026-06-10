# Architecture Overview

## High-Level Flow

```text
Scraping -> ETL -> Geocoding/Enrichment -> Valuation -> Scoring -> Dashboard/Notifications
```

## Core Components

- **Scraping**: Collects listings from real-estate portals
- **ETL**: Normalizes and deduplicates listings
- **Database**: Stores raw, clean, valuation, and scoring data
- **Valuation Engine**: Estimates fair value using model ensemble logic
- **Scoring Engine**: Ranks opportunities by investment quality
- **Dashboard**: Streamlit interface for operators
- **Monitoring**: Health checks, metrics, and logs
- **Scheduler**: Runs the pipeline on a schedule

## Runtime Directories

- `data/`: persistent data, exports, and backups
- `logs/`: runtime logs and archived outputs
- `scripts/`: operational scripts and launchers
- `tests/`: automated tests and validation checks
- `docs/`: user and technical documentation

## Notes

The repository has been cleaned to keep temporary scripts and reports out of the root directory. This improves maintenance and makes the project easier to hand over to a client.
