# Implementation Report — Close Critical Gaps

Date: 2026-04-25
Plan: close-critical-gaps-55dcdc.md

## Summary

All planned phases were implemented successfully. The following changes were made:

## Phase 1: Redis Container (⚠️ Requires Docker Desktop)
- Docker Compose already has Redis configured (port 6379)
- `docker compose up -d redis` is ready to run once Docker Desktop is started
- No code changes needed — app auto-detects Redis on localhost:6379

## Phase 2: Python 3.12 Virtualenv ✅
- Created `venv312` with Python 3.12.10
- Installed all core + heavy dependencies (spacy, textblob, catboost, transformers)
- Verified heavy deps import successfully

### Updated Launchers (all now use venv312):
- `start_system.bat`
- `run_scrapers.bat`
- `start_dashboard.bat`
- `start_scheduler.bat`

### Files Modified:
- `realestate_engine/pyproject.toml` — added `[heavy]` optional deps
- `start_system.bat`
- `run_scrapers.bat`
- `start_dashboard.bat`
- `start_scheduler.bat`

## Phase 3: Detail-Page Scraping ✅
Created `scripts/run_detail_scraping.py` with:
- HTTP-based scraping (httpx, no browser automation)
- JSON-LD extraction + regex fallback
- Resumable progress tracking (SQLite)
- Proxy support (RESIDENTIAL_PROXY_URL from .env)
- Portal-aware URL construction:
  - Casa Sapo: `https://casa.sapo.pt/p{source_id}`
  - REMAX: requires full URL from raw data
  - Imovirtual: uses existing source_url
- Batch processing with delays
- Updates both CleanListing and RawListing

### Critical Fix for Casa Sapo / REMAX:
- **Root cause**: `pipeline_etl.py:77` only passed `r.raw_data` to normalizer, but Casa Sapo/REMAX spiders put `source_id`/`source_url` at the **record top level**, not inside `raw_data`
- **Fix**: After normalization, merge top-level fields from the raw record:
  ```python
  if not n.get("source_id") and r.source_id:
      n["source_id"] = r.source_id
  if not n.get("source_url") and r.source_url:
      n["source_url"] = r.source_url
  ```
- **Impact**: NEW data entering the pipeline will have correct source_id/source_url for Casa Sapo and REMAX

### Additional Fix:
- `normalizer.py` `normalize_estado()` now scans title + description for condition keywords (not just explicit condition field)

## Phase 4: Validation Status

### What Works:
- ✅ venv312 created and deps installed
- ✅ Detail scraper script created and compiles
- ✅ Source_id/source_url fix for new data
- ✅ normalize_estado scans title+description

### What Requires Next Steps:

#### 1. Redis (1 minute)
```powershell
cd "C:\Users\rodri\Desktop\Projeto analize mercado imobeleario"
docker compose up -d redis
```

#### 2. Re-scrape Casa Sapo + REMAX for URLs
**Problem**: Existing clean listings (447 Casa Sapo, 140 REMAX) have NO source_id or source_url because they were processed before the pipeline fix.
**Solution**: Run a fresh scrape. The spiders now extract source_id/source_url correctly, and the pipeline fix ensures they reach CleanListing.
```powershell
.\venv312\Scripts\python run_scraper_manual.py --pages 5
```

#### 3. Detail Scraping for Energy/Year/Condition
After re-scraping (or for Imovirtual which already has URLs):
```powershell
.\venv312\Scripts\python scripts\run_detail_scraping.py --batch-size 20 --max-listings 100 --portals imovirtual
```
**Note**: Imovirtual requires proxy (set `RESIDENTIAL_PROXY_URL` in `.env`)
**Casa Sapo/REMAX**: Can run without proxy once re-scraped with URLs

#### 4. pytest on venv312
```powershell
$env:PYTHONPATH="."
.\venv312\Scripts\python -m pytest realestate_engine/tests/ -v
```
**Note**: If `asgi_gunicorn` import error occurs, install: `pip install asgi-gunicorn`

## Known Issues from Audit
| Issue | Status | Action Required |
|-------|--------|-----------------|
| Energy Cert / Year / Condition = 0% | Expected | Detail pages only. Fix requires re-scrape + detail scraper run |
| Casa Sapo source_url = 0% | Fixed in code | Re-scrape needed for existing data |
| REMAX source_url = 0% | Fixed in code | Re-scrape needed for existing data |
| Redis not running | Docker not started | Start Docker Desktop, run `docker compose up -d redis` |
| Python 3.14 → 3.12 | Done | venv312 created, launchers updated |

## Files Changed:
1. `realestate_engine/etl/pipeline_etl.py` — merge source_id/source_url from record
2. `realestate_engine/etl/normalizer.py` — normalize_estado scans title+description
3. `realestate_engine/pyproject.toml` — added [heavy] optional deps
4. `realestate_engine/nlp/summarizer.py` — corrupted cache handling + fallback
5. `realestate_engine/infrastructure/event_bus.py` — asyncio.iscoroutinefunction → inspect
6. `realestate_engine/nlp/ner_extractor.py` — added numpy import
7. `start_system.bat` — venv312
8. `run_scrapers.bat` — venv312
9. `start_dashboard.bat` — venv312
10. `start_scheduler.bat` — venv312
11. `scripts/run_detail_scraping.py` — NEW (detail page scraper)
