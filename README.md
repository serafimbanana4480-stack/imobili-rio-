# Real Estate Opportunity Engine — Grande Porto

Motor autónomo de análise do mercado imobiliário português com scraping multi-portal,
ETL com deduplicação, valuation, scoring de oportunidades, notificações Telegram,
dashboard Streamlit, e tese de investimento por LLM local (Ollama).

---

## Quick start (Windows)

```bat
start.bat install      :: Setup inicial (venv, dependências slim, DB)
start.bat doctor       :: Verifica ambiente (Python, browser, DB)
start.bat dashboard    :: Abre dashboard + API em janelas separadas
```

## Quick start (macOS / Linux)

```bash
chmod +x start.sh           # primeira vez
./start.sh install          # Setup inicial (venv312, deps, DB)
./start.sh doctor           # Verifica ambiente
./start.sh dashboard        # Abre dashboard + API
```

Os comandos são paritários ao `start.bat` (`install`/`doctor`/`api`/`ui`/`dashboard`/
`engine`/`all`/`test`/`help`/`menu`). Em macOS abre janelas no `Terminal.app` via AppleScript;
em Linux tenta `gnome-terminal` ou `x-terminal-emulator`; em ambientes headless cai para
background processes.

| URL | Descrição |
|---|---|
| http://localhost:8501 | Dashboard Streamlit |
| http://localhost:8000 | API REST (FastAPI) |
| http://localhost:8000/docs | Swagger / OpenAPI |

### Outros comandos

```bat
start.bat engine       :: Pipeline 24h autónomo (foreground)
start.bat all          :: Engine + dashboard + API
start.bat api          :: Só a API
start.bat ui           :: Só a dashboard
start.bat test         :: Suite pytest completa (29 testes)
start.bat help         :: Ajuda
```

### Extras opcionais

A install default é slim (~200 MB). Para activar análise de imagens ou NLP avançado:

```bat
venv312\Scripts\activate
pip install -e realestate_engine[cv]    :: ~200 MB - image quality, pHash, YOLO
pip install -e realestate_engine[nlp]   :: ~2 GB   - BERT sentiment, NER, summarisation
pip install -e realestate_engine[all]   :: tudo
```

*A omissão dos extras não impede o pipeline de arrancar — os enrichers pesados ficam
automaticamente desactivados (ver `PRODUCTION_READINESS.md`, fix B1).*

# imobili-rio-

---

## Arquitetura

```
realestate_engine/
├── api/              FastAPI REST + Pydantic schemas
├── dashboard/        Streamlit (app.py + views/ lazy-loaded)
├── database/         SQLAlchemy 2.x (repository.py, models.py)
├── etl/              Normalização, deduplicação, enriquecimento
├── scraping/
│   ├── browser_resolver.py   Auto-deteção Chrome/Chromium
│   └── spiders/              Nodriver + spiders directos
├── valuation/        Modelo de avaliação + cliente INE
├── scoring/          Scoring multi-fator de oportunidade
├── monitoring/       Health checks, métricas Prometheus
└── notifications/    Telegram bot
```

---

## Spiders e browser

Os spiders Nodriver (`era`, `supercasa`, `century21`, `olx`) precisam de Chrome
ou Chromium local. O `browser_resolver` deteta automaticamente em Windows,
macOS e Linux. Para forçar um caminho específico:

```bat
set REE_CHROME_PATH=C:\Path\To\chrome.exe
```

Spiders que **não** precisam de browser: `imovirtual` (Next.js JSON),
`casa_sapo` (JSON-LD), `remax` (sitemap).

---

## Configuração

Copia `.env.example` para `.env` e preenche o que precisares:

- `DATABASE_URL` — default Postgres; alternativa `sqlite:///data/db/realestate.db`
- `REDIS_URL` / `REDIS_REQUIRED` — cache + rate-limit por portal
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — notificações (Phase 5)
- `RESIDENTIAL_PROXY_URL` — Smartproxy/Oxylabs para scraping production
- `REE_CHROME_PATH` — opcional, override do browser
- `OLLAMA_HOST` / `OLLAMA_MODEL` — LLM local para a view "Melhores Deals IA"
  (default `http://localhost:11434` / `mistral:7b`; podes apontar para
  `qwen3-14b-fast` ou `qwen3-35b-q4` mudando só esta variável)
- `ENRICH_SKIP_HEAVY` — `1` para saltar CV/NLP em runs rápidos

---

## Testes

```bat
start.bat test       :: Windows
./start.sh test      :: macOS / Linux
```

Duas suites pytest:

- **`tests/` (raiz)** — **29 testes** curados, end-to-end e regressão production-readiness.
  `start.bat test` / `./start.sh test` corre apenas esta.
- **`realestate_engine/tests/`** — ~305 testes unit/integration mais granulares (cobrem
  CV, NLP, validators, etc.). Muitos requerem extras `[cv]`/`[nlp]`. `pytest.ini` inclui
  ambos os caminhos em `testpaths`, portanto `pytest` sem args corre tudo.

---

## Stack

- **Python 3.12**, SQLAlchemy 2.x, Pydantic v2, FastAPI, Streamlit
- **Scraping:** Nodriver (undetected Chrome), httpx, BeautifulSoup
- **Dados:** SQLite (default) ou Postgres via `DATABASE_URL`
- **Monitoring:** Prometheus, loguru, health checks

---

## Estado

- ✅ 8 portais cobertos (casa_sapo, era, idealista, imovirtual, remax, supercasa, olx,
  century21) servidos por 12 spiders (alguns portais têm variantes Nodriver + directo)
- ✅ Valuation com 4 modelos + meta-ensemble (Hedónico, Comparáveis, INE, XGBoost) e SHAP
- ✅ 15 views Streamlit (Overview, Search, Market Analysis, Investor Tools, Score Audit,
  Watchlist, Map, AI Deals, Telegram, Config, System, Pipeline Status, Data Quality,
  Debug Logs, Scraping Results)
- ✅ ACID transactions com auto-rollback
- ✅ Dashboard com lazy-loading e error boundaries por view
- ✅ Auto-deteção de browser cross-platform
- ✅ Health checks + métricas Prometheus
- ⏳ Paridade `start.sh` macOS/Linux pendente (Onda 2 do roadmap de produção)
- ⏳ Auditoria do scheduler 24h pendente (Onda 4 do roadmap de produção)

Ver `PRODUCTION_READINESS.md` para o roadmap completo de hardening e o que falta antes
de uso comercial.

---

## Documentação

- `PRODUCTION_READINESS.md` — Auditoria de produção e roadmap de hardening
- `docs/COMO_USAR.md` — Manual de utilização
- `docs/ARCHITECTURE.md` — Arquitetura detalhada
- `docs/API.md` — Referência da API REST
- `docs/como_usar/` — Guias rápidos
- `docs/reports/` — Relatórios técnicos e auditorias

---

## Troubleshooting

### "Diagnóstico: {'error': 'timeout'}" na view AI Deals

O modelo Ollama em cold-start (primeira chamada após boot) pode demorar > 60 s a
carregar pesos do disco. A correcção (Onda 1, fix B3) já inclui warm-up + retry +
`keep_alive=30m`, mas se persistir:

1. Verifica que o `ollama serve` está a correr: `curl http://localhost:11434/api/tags`
2. Confirma que o modelo está pulled: `ollama list` deve mostrar `mistral:7b`. Se não:
   `ollama pull mistral:7b`.
3. Em CPU lento ou modelos grandes, aumenta `OLLAMA_READ_TIMEOUT_S=300` no `.env`.
4. Se queres trocar de modelo, basta mudar `OLLAMA_MODEL` no `.env` (sem código).

### `ModuleNotFoundError: torch` ao correr o ETL

A install default é slim e não inclui torch/transformers. Duas opções:

- **Continuar slim:** garante que `ENRICH_SKIP_HEAVY=1` está no `.env`. Os enrichers
  CV/NLP ficam a no-op silenciosamente.
- **Instalar extras:** `pip install -e realestate_engine[cv,nlp]` (~3 GB).

### Spider Nodriver não arranca

Nodriver precisa de Chrome ou Chromium local. O `browser_resolver` deteta
automaticamente em Windows/macOS/Linux mas se falhar:

```bash
# Windows
set REE_CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
# macOS
export REE_CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

Spiders sem necessidade de browser: `imovirtual` (Next.js JSON), `casa_sapo`
(JSON-LD), `remax` (sitemap).

---

## Licença

Propriedade privada. Contacta o autor para licenciamento.
