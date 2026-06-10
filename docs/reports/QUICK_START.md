# Quick Start Guide

Get the Real Estate Intelligence Engine running in 5 minutes.

## Prerequisites
- Windows 10/11, Linux, or macOS
- Python 3.12+ installed
- 8GB RAM minimum

## Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd <project-directory>
python -m venv venv312
venv312\Scripts\activate  # Windows
# source venv312/bin/activate  # Linux/macOS
```

### 2. Install Dependencies
```bash
cd realestate_engine
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your settings (optional for basic use)
```

### 4. Initialize Database
```bash
python -c "from realestate_engine.database.models import init_db; from realestate_engine.utils.config import config; init_db(config.database_url)"
```

## Start the System

### Option A: Quick Start (HTTP)
```bash
start_all.bat
```

### Option B: Autonomous 24H Engine
```bash
start_engine_24h.bat
```

### Option C: Dashboard + API
```bash
start_dashboard_backend.bat
```

### Option D: Manual Start
```bash
# Terminal 1 - API
cd realestate_engine
python -m api.main

# Terminal 2 - Dashboard
cd realestate_engine/dashboard
streamlit run app.py --server.port 8501
```

## Access

- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## First Steps

1. **Scrape Data**: Go to Dashboard → Sistema → Executar Scraping
2. **Run Pipeline**: Click Pipeline Completo to process data
3. **View Opportunities**: Navigate to Overview to see top deals
4. **Search**: Use Pesquisa & Filtros to find specific properties

## Troubleshooting

**Port already in use?**
- Change port in start_dashboard_backend.bat or use different ports

**Dependencies error?**
- Ensure Python 3.12+ is installed
- Run `pip install --upgrade pip`

**Database error?**
- Delete `data/db/realestate.db` and reinitialize

## Need Help?

See full documentation in `SALE_DOCUMENTATION.md`
