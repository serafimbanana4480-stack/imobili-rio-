# Real Estate Opportunity Engine

Sistema autónomo de análise de mercado imobiliário em Portugal para identificar oportunidades de investimento, com foco inicial no mercado do Porto.

## 🏗️ Arquitetura

O sistema implementa uma arquitetura em camadas com pipeline completo:

- **Scraping Layer**: Nodriver + curl-cffi servindo 8 portais imobiliários (Idealista,
  Imovirtual, Casa Sapo, ERA, REMAX, OLX, Century21, SuperCasa) através de 12 spiders
  (alguns portais têm variantes Nodriver + directo via JSON-LD/sitemap)
- **ETL Layer**: Normalização, deduplicação, geocodificação, enriquecimento com dados INE e POI;
  enrichers CV/NLP opcionais (lazy-loaded, ver fix B1 em `PRODUCTION_READINESS.md`)
- **Valuation Layer**: 4 modelos + meta-ensemble (Hedónico, Comparáveis, INE, XGBoost,
  Weighted/Advanced ensemble) com SHAP explanations
- **Scoring Layer**: Algoritmo multi-factor (Discount 45% + Location 20% + Condition 15% +
  Liquidity 10% + Freshness 10%)
- **Notification Layer**: Telegram bot para oportunidades com score ≥ 8
- **Dashboard Layer**: 15 views Streamlit lazy-loaded com error boundaries
- **AI Deals**: Cliente Ollama local (mistral:7b por defeito; configurável via
  `OLLAMA_MODEL`) para geração de tese de investimento por LLM
- **Scheduler Layer**: APScheduler com dependências entre jobs
- **Monitoring Layer**: Loguru + Prometheus + Health checks + Error tracking

## 📁 Estrutura do Projeto

```
realestate_engine/
├── scraping/          # Spiders e anti-bot evasion
│   └── spiders/       # Spiders para cada portal
├── etl/              # Pipeline ETL
│   ├── normalizer.py  # Normalização de dados
│   ├── deduplicator.py # Detecção de duplicados
│   ├── geocoder.py    # Geocodificação
│   └── enricher.py    # Enriquecimento com INE/POI
├── valuation/        # Motor de avaliação (4 modelos + meta-ensemble)
│   ├── hedonic_model.py
│   ├── comps_engine.py
│   ├── ine_client.py
│   ├── xgboost_model.py
│   ├── weighted_ensemble.py
│   ├── advanced_ensemble.py
│   ├── confidence_interval.py
│   └── valuation_engine.py
├── cv/               # OPCIONAL: image quality + similarity (extra `cv`)
├── nlp/              # OPCIONAL: BERT sentiment + NER + summarisation (extra `nlp`)
├── features/         # Micro-location + NLP rápido (regex)
├── investor_tools/   # ROI calculators + LLM analyzer (Ollama)
├── quality/          # Data quality monitoring
├── api/              # FastAPI REST + Pydantic schemas
├── infrastructure/   # Cache + utilities
├── migrations/       # Alembic migrations
├── scoring/          # Motor de scoring
│   ├── scoring_engine.py
│   ├── score_*_calculator.py
│   └── red_flags_detector.py
├── database/         # Models e repository
│   ├── models.py      # SQLAlchemy models
│   └── repository.py  # Database operations
├── notification/     # Notificações Telegram
├── dashboard/        # Streamlit dashboard
│   └── views/        # Dashboard pages
├── scheduler/        # Orquestração de jobs
├── monitoring/       # Métricas e health checks
├── security/         # Encriptação e rate limiting
├── utils/            # Config, logger, decorators
├── tests/            # PLACEHOLDER do roadmap original (vazio, não usado)
│                     # A suíte real está em `tests/` na raiz do projeto
├── data/             # DB, backups, cache
│   ├── db/
│   ├── backups/
│   ├── cache/
│   └── logs/
└── .github/workflows/# CI/CD
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.12 (recomendado pelo `nodriver`)
- PostgreSQL (produção) ou SQLite (dev local)
- Redis (opcional, para cache + rate-limit)
- Ollama (opcional, para a view AI Deals)

### Instalação (Windows)

Usa o launcher na raiz do repositório:

```bat
start.bat install      :: Cria venv312, instala editável, prepara DB
start.bat doctor       :: Verifica ambiente
start.bat dashboard    :: Lança UI + API
```

### Instalação (macOS / Linux)

```bash
chmod +x start.sh
./start.sh install
./start.sh doctor
./start.sh dashboard
```

### Instalação manual (alternativa ou para extras opcionais)

```bash
python3.12 -m venv venv312 && source venv312/bin/activate
pip install -e .                    # Slim install (~200 MB)
pip install -e .[cv,nlp]            # OPCIONAL: extras pesados (~3 GB)
pip install -e .[dev]               # OPCIONAL: pytest, black, mypy

cp .env.example .env                # Editar com as tuas configurações
```

### Executar testes

Há duas suites; ver secção "Testes" do `README.md` da raiz para o detalhe.

```bash
# Suite curada (29 testes, rápida) — a que start.bat/start.sh test corre:
pytest tests/ -v

# Tudo: 29 + ~305 unit/integration aqui em realestate_engine/tests/
pytest -v
```

Os ~305 unit tests cobrem CV, NLP, validators e cobertura granular; alguns
requerem extras `[cv]`/`[nlp]` instalados.

## 🔧 Configuração

Variáveis de ambiente principais (`.env`):

```env
# Database
DATABASE_URL=sqlite:///data/db/realestate.db

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Scheduler intervals (minutos)
SCRAPING_INTERVAL_MINUTES=30
ETL_INTERVAL_MINUTES=32
VALUATION_INTERVAL_MINUTES=35
SCORING_INTERVAL_MINUTES=38
NOTIFICATION_INTERVAL_MINUTES=60
```

## 📊 Dashboard

15 views Streamlit lazy-loaded, agrupadas por uso:

- **Decisão**: Overview, Search, Watchlist, Map View, **AI Deals** (LLM tese)
- **Análise**: Market Analysis, Investor Tools (ROI), Score Audit
- **Operação**: Pipeline Status, Scraping Results, Data Quality, System
- **Configuração**: Config, Telegram, Debug Logs

## 🔍 Troubleshooting

Para os 3 erros mais comuns (Ollama timeout, ETL ImportError, Chrome não encontrado),
ver a secção **Troubleshooting** no `README.md` da raiz, ou `PRODUCTION_READINESS.md`
para o roadmap completo de hardening.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Abra Pull Request

## 📝 Licença

MIT License - ver arquivo LICENSE para detalhes

## 📞 Suporte

Para questões ou bugs, abra uma issue no GitHub.
