# Production Setup — Runbook

This is the **only** supported procedure to bring the engine up with real data.
Any deviation (SQLite in prod, missing proxies, empty Telegram token) will
cause the bootstrap check to fail loudly.

---

## 0. Prerequisites

- Docker Desktop running (for `docker compose`)
- Python 3.11+ (3.14 tested)
- A paid residential proxy account (BrightData, Oxylabs, Smartproxy)
- A Telegram bot (token via `@BotFather`) and destination chat id

---

## 1. Configure environment

```powershell
copy .env.example .env
notepad .env
```

Fill in at minimum:

- `DATABASE_URL` — keep the default Postgres DSN unless you changed credentials
- `REDIS_URL` — leave default if running Redis locally via Docker
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `RESIDENTIAL_PROXY_URL` — e.g.
  `http://user-sessionrand:password@gate.smartproxy.com:7000`

---

## 2. Start infrastructure

```powershell
docker compose up -d postgres redis
docker compose ps
```

Wait until both report `healthy`.

---

## 3. Install Python deps

```powershell
pip install -r realestate_engine\requirements.txt
pip install psycopg2-binary redis python-dotenv
```

---

## 4. Run the production bootstrap check

```powershell
python -m realestate_engine.infrastructure.bootstrap
```

Expected output:

```
✅ PostgreSQL reachable at localhost:5432/realestate
✅ Redis healthy at redis://localhost:6379/0
✅ Residential proxy configured
✅ Telegram bot healthcheck OK (message sent)
🎉 All checks passed — system is ready for real scraping
```

If **any** line is `❌`, fix it before continuing. The engine refuses to run
on a degraded infrastructure.

---

## 5. Start the 24/7 scheduler

```powershell
python -m realestate_engine.main
```

This starts the APScheduler loop. Cycles run from 08:00 to 22:00; the first
cycle triggers at the top of the next hour.

To force an immediate cycle for validation, open a second terminal:

```powershell
python -c "import asyncio; from realestate_engine.scheduler.orchestrator import Orchestrator; asyncio.run(Orchestrator().run_full_pipeline())"
```

---

## 6. Start the dashboard

```powershell
streamlit run realestate_engine\dashboard\app.py
```

The sidebar shows a green data-source banner with the live Postgres row
count. If it shows 0, the pipeline has not produced data yet.

---

## 7. Verify job_execution_log

```powershell
docker exec -it realestate_postgres psql -U realestate -d realestate -c "SELECT job_name, status, records_processed, started_at FROM job_execution_log ORDER BY id DESC LIMIT 20;"
```

Every scraping / ETL / valuation / scoring / notification cycle must leave a
row here. Empty = something is skipping the JobLogger wrapping.

---

## 8. Sanity: no fake data can exist

```powershell
docker exec -it realestate_postgres psql -U realestate -d realestate -c "SELECT COUNT(*) FROM raw_listings WHERE is_sample = 1;"
```

Must always return `0`. The `generate_sample_data` utility has been removed
from the codebase, so no process can insert a synthetic row.

---

## 9. Running tests (no mocks)

```powershell
pytest realestate_engine\tests -x
```

The integration test in `tests/integration/test_full_pipeline.py` no longer
imports `generate_sample_data`; it seeds the DB with real-shape `RawListing`
rows and exercises the full pipeline.

---

## Troubleshooting

| Symptom | Root cause |
|---|---|
| `Python was not found` | Use `py` instead of `python` on Windows |
| Bootstrap: `❌ PostgreSQL unreachable` | `docker compose up -d postgres` not executed, or port 5432 blocked |
| Bootstrap: `❌ Telegram healthcheck failed` | Token revoked, chat id wrong, or bot never sent `/start` |
| Scraping cycle reports 0 listings across all portals | Residential proxy not active — Idealista/Imovirtual block datacenter IPs |
| Dashboard banner says `Data source unreachable` | `DATABASE_URL` env not exported or Postgres container stopped |
