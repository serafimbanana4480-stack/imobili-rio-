# Real Estate Opportunity Engine

Este pacote contém o código principal do motor de análise imobiliária.

## 📖 Documentação Principal

Para documentação completa, instruções de instalação e uso, consulte o **[README.md na raiz do projeto](../README.md)**.

## 📁 Estrutura do Pacote

```
realestate_engine/
├── scraping/          # Spiders e anti-bot evasion
│   └── spiders/       # Spiders para cada portal
├── etl/              # Pipeline ETL
├── valuation/        # Motor de avaliação (4 modelos + meta-ensemble)
├── scoring/          # Motor de scoring
├── database/         # Models e repository
├── api/              # FastAPI REST + Pydantic schemas
├── dashboard/        # Streamlit dashboard
├── scheduler/        # Orquestração de jobs
├── monitoring/       # Métricas e health checks
├── security/         # Encriptação e rate limiting
├── utils/            # Config, logger, decorators
└── data/             # DB, backups, cache
```

## 🚀 Instalação

```bash
# Slim install (~200 MB)
pip install -e .

# Extras opcionais
pip install -e .[cv,nlp]  # ~3 GB - image quality, BERT, etc.
pip install -e .[dev]     # pytest, black, mypy
```

## 🧪 Testes

```bash
# Suite curada (29 testes)
pytest ../tests/ -v

# Tudo: 29 + ~305 unit/integration
pytest -v
```

## � Suporte

Para questões ou bugs, consulte o README.md na raiz do projeto.
