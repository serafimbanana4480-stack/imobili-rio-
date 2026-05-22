# Production Readiness Audit — Real Estate Opportunity Engine

> **Data:** 2026-04-29
> **Âmbito:** auditoria estrutural, dependências, scripts, testes, bugs específicos, IA, Telegram, UI
> **Método:** leitura directa do código + verificação por citações de ficheiro:linha
> **Estado global:** **NÃO PRONTO PARA VENDA** — existem 3 bloqueadores críticos antes da camada cosmética

---

## 0. TL;DR — o que precisa de acontecer antes de comercializar

| # | Item | Severidade | Esforço estimado |
|---|---|---|---|
| **B1** | ETL crasha no boot porque `enricher.py` faz imports duros de `cv/nlp/features` mas o `start.bat install` não instala torch/transformers/ultralytics | 🔴 **Bloqueador** | 30 min |
| **B2** | `requirements.txt` (~3 GB de torch/CUDA/ultralytics/transformers) está desalinhado de `pyproject.toml` (slim) — fonte de verdade ambígua | 🔴 **Bloqueador** | 1 h |
| **B3** | `OpportunityAnalyzer` faz hard-code de `http://localhost:11434`, sem retries, sem warm-up, e o timeout de 60 s é demasiado curto para cold-start de `mistral:7b` em CPU → "Diagnóstico: {'error': 'timeout'}" no print do utilizador | 🟠 **Crítico** | 1 h |
| H1 | Sem `start.sh` para macOS com paridade ao `start.bat` (o existente em `macos/start_all.sh` falta `install`/`doctor`/`engine`/`test`) | 🟠 Alto | 1 h |
| H2 | Estrutura de testes fragmentada: `tests/` (raiz, ~22 ficheiros) + `realestate_engine/tests/` (paralela). README diz "22 passing" mas há ~50 ficheiros no total | 🟠 Alto | varia |
| H3 | UI dark-mode com tabelas de baixo contraste (screenshot do utilizador confirma) | 🟡 Médio | 1 h |
| M1 | Sem testes de regressão para os bugs já corrigidos: `DetachedInstanceError` em `score_audit`, e contraste do dark-mode em `system.py` | 🟡 Médio | 1 h |
| M2 | Documentação inconsistente já levantada em `RELATORIO_INCONSISTENCIAS.md` — não foi reconciliada | 🟡 Médio | 1–2 h |
| L1 | Bot Telegram sem reconnect/backoff documentado (verificar) | 🔵 Baixo | 30 min |

---

## 1. Bloqueadores críticos

### B1. ETL crasha no boot — imports duros de stack pesada

`@c:/Users/rodri/Desktop/Projeto analize mercado imobeleario/realestate_engine/etl/enricher.py:30-37`
```python
from realestate_engine.features.micro_location import extract_micro_location_features
from realestate_engine.features.nlp_portuguese import analyze_portuguese_description
from realestate_engine.cv.image_quality import ImageQualityAnalyzer
from realestate_engine.cv.image_similarity import ImageSimilarityDetector
from realestate_engine.nlp.bert_portuguese import BERTPortugueseProcessor
from realestate_engine.nlp.sentiment_analyzer import SentimentAnalyzer
from realestate_engine.nlp.ner_extractor import NERExtractor
from realestate_engine.nlp.summarizer import DescriptionSummarizer
```

E os módulos importam `torch`, `transformers`, `ultralytics` no top-level. Mas `pyproject.toml` (que é o que `start.bat install` instala em `@c:/Users/rodri/Desktop/Projeto analize mercado imobeleario/start.bat:131`) **não** declara essas dependências:

`@c:/Users/rodri/Desktop/Projeto analize mercado imobeleario/realestate_engine/pyproject.toml:28-54` — sem torch/transformers/ultralytics.

**Consequência:** após `start.bat install`, qualquer execução do ETL ou do `main_engine` falha com `ModuleNotFoundError: torch`. Isto é silencioso até alguém correr o pipeline pela primeira vez.

**Fix recomendado:**
1. Tornar `cv/nlp/features` imports **lazy** dentro de métodos com `try/except ImportError` + flag `ENRICH_SKIP_HEAVY` (já existe em `start.bat:203` mas não é honrada por imports top-level).
2. Acrescentar `[project.optional-dependencies]` `cv`, `nlp`, `heavy` em `pyproject.toml` e documentar `pip install -e .[cv,nlp]` para quem quer.
3. Default ship sem stack pesada → produto comercializável fica pequeno (<200 MB).

### B2. `requirements.txt` desalinhado de `pyproject.toml`

- `requirements.txt` tem `torch`, `torchvision`, `ultralytics`, `transformers`, `accelerate`, `sentencepiece`, `opencv-python`, `pillow`, `imagehash` → ~3 GB.
- `pyproject.toml` (instalado por `start.bat install`) **não** os declara.
- README global diz "instala via `start.bat install`" mas o `requirements.txt` faria download de 3 GB.

**Fix:** eliminar `requirements.txt` ou regenerá-lo a partir de `pyproject.toml` (apenas extras instalados). Decisão arquitectónica: queremos que o produto inclua CV/NLP por default ou seja opcional? **Recomendo opcional** (B1 fix) — torna o produto vendável sem GPU/3 GB de dependências.

### B3. AI Best Deals timeout / fallback constante

`@c:/Users/rodri/Desktop/Projeto analize mercado imobeleario/realestate_engine/investor_tools/opportunity_analyzer.py:66-99`

Problemas concretos:
1. **URL hardcoded:** `"http://localhost:11434/api/generate"` — não respeita `OLLAMA_HOST` ou `.env`.
2. **Modelo hardcoded** no construtor: `model: str = "mistral:7b"` — utilizador tem `qwen3-14b-fast.modelfile` e `qwen36-35b-q4.modelfile` no projeto mas nunca usados.
3. **Sem warm-up:** primeiro `/api/generate` num modelo cold faz load do modelo do disco (mistral:7b ~4 GB; qwen3-14b ~9 GB) → > 60 s em CPU/SSD lento.
4. **Sem retry:** uma falha transitória dá fallback definitivo nessa run.
5. **Sem cache:** mesma listing é reanalisada de cada vez (custo + risco de timeout repetido).
6. **Logs pobres:** `last_diagnostic` é guardado em memória da instância — perdido entre runs do Streamlit.

**Fix recomendado (mínimo viável):**
- Ler `OLLAMA_HOST` (default `http://localhost:11434`) e `OLLAMA_MODEL` (default `mistral:7b`) do `.env`.
- Endpoint `/api/show` antes de `/api/generate` para confirmar modelo carregado; se 404 → mensagem clara "corre `ollama pull <model>`".
- Endpoint `/api/generate` com `keep_alive: "30m"` para evitar reload.
- Warm-up call de prompt curto antes do batch real, com timeout próprio de 120 s.
- Timeouts separados: `connect=5s`, `read=180s`.
- 1 retry com backoff em `ReadTimeout`.
- Cache `(listing_id, model) → thesis` em SQLite via `data/cache/`.
- Logging estruturado: `logger.info("ollama call", extra={"model":..., "ms":..., "fallback": False})`.

---

## 2. Auditoria geral — código morto, módulos, dependências

### 2.1 Módulos avançados — decisão pendente
Existem mas estão dependentes de stack pesada não instalada por default:
- `realestate_engine/cv/` — `image_quality.py`, `image_similarity.py`, `room_detector.py` (usa ultralytics YOLO)
- `realestate_engine/nlp/` — `bert_portuguese.py`, `sentiment_analyzer.py`, `ner_extractor.py`, `summarizer.py`
- `realestate_engine/features/nlp_portuguese.py` — duplica funcionalidade de `nlp/`

**Recomendação:** consolidar em `nlp/` (eliminar `features/nlp_portuguese.py` se duplicar) e marcar `cv/` + `nlp/` como **optional extras**. Manter `features/micro_location.py` que é leve.

### 2.2 Scripts de debug acumulados
- `scripts/debug/` tem 46 ficheiros `.py` (`_debug_*`, `_diagnose_*`, etc.) — não são código de produção.
- `logs/` tem 57 ficheiros incluindo logs antigos (`_pipeline_run2.log`, `_probe_*.txt`).

**Recomendação:** mover `scripts/debug/` para `.gitignore` ou para uma pasta `internal/` excluída do produto vendido. Limpar `logs/` antigos.

### 2.3 Estrutura de testes duplicada
- `tests/` na raiz (~22 ficheiros) — alvo do `start.bat test`
- `realestate_engine/tests/` — paralela, com `unit/`, `integration/`, `e2e/` (também referida pela documentação)

**Recomendação:** eleger uma das duas. README global aponta para a da raiz (`pytest tests/`), mas o `realestate_engine/README.md:103-112` aponta para `pytest tests/unit/` (a interna). Inconsistência grave. **Sugiro consolidar em `tests/` na raiz com subdirs `unit/integration/e2e/`** e apagar `realestate_engine/tests/`.

---

## 3. Instalação e execução

### 3.1 `start.bat` — análise
Bom: estrutura de subcomandos clara, doctor, fallback de porta 8000→8001, lança em janelas separadas.
Lacunas:
- `:install` não instala `pip install -e ".[dev]"` → utilizador não tem `pytest` → `start.bat test` quebra em ambiente fresco.
- Não verifica versão Python (>=3.10 recomendado por `nodriver`).
- Não cria `.env` a partir de `.env.example` se faltar.
- `:doctor` não verifica conectividade ao Ollama nem ao Telegram.

### 3.2 macOS — `macos/start_all.sh`
Existe mas é um stub: lança API + dashboard com `&`, sem `install`, `doctor`, `engine`, `test`, sem detecção de venv, sem fallback de porta. **Falta paridade total com `start.bat`.**

**Fix:** criar `start.sh` na raiz com os mesmos subcomandos (`install`/`doctor`/`api`/`ui`/`dashboard`/`engine`/`all`/`test`). Bash + `set -euo pipefail`. Manter `macos/start_all.sh` como wrapper.

---

## 4. Bug: `DetachedInstanceError` no `score_audit`

**Estado actual:** `@c:/Users/rodri/Desktop/Projeto analize mercado imobeleario/realestate_engine/dashboard/views/score_audit.py:30-37` já usa `selectinload(Score.listing).selectinload(CleanListing.valuations)` dentro do `with repo.Session()`. **O bug parece já estar fixed.**

**Falta:** teste de regressão. Recomendo adicionar `tests/test_score_audit_regression.py` que:
1. Cria `Score` + `CleanListing` + `Valuation` em memória (SQLite `:memory:`).
2. Renderiza a view via `streamlit.testing.v1.AppTest` ou apenas chama a função e verifica que acede a `score.listing.valuations[0]` fora do `with session` sem `DetachedInstanceError`.

---

## 5. Bug: dark-mode na página `system.py` e tabelas

**Screenshot fornecido pelo utilizador:** tabelas em tema escuro com células brancas e texto cinza-claro → ilegíveis.

**Causa provável:** `st.dataframe()` por default usa o tema Streamlit, mas `st.markdown` com HTML inline (que existe em vários views, ex: `ai_deals.py:80-94`) força cores claras (`color:#6B7280`) que ficam invisíveis em fundo escuro.

**Fix:** adicionar CSS global em `dashboard/utils/theme.py` com `[data-theme="dark"]` overrides e `prefers-color-scheme`. Aplicar via `st.markdown(STYLES, unsafe_allow_html=True)` no `app.py` antes de qualquer view.

**Ainda preciso de ler:** `system.py` e `dashboard/utils/theme.py` para diagnosticar com precisão. Marcar antes de aplicar fix.

---

## 6. Modo 24h

`main_engine.py` (1.4 KB) e `scheduler/` — não auditado em profundidade. Verificações pendentes:
- Loops sem `await asyncio.sleep` → CPU 100%
- Re-entrancy de jobs APScheduler (max_instances)
- Persistência de estado entre crashes (jobstores)
- Memory leak em `Enricher` (lru_cache cresce sem limite com novas keys)

---

## 7. Bot Telegram

`notification/notification_engine.py` referenciado mas não auditado em profundidade. Verificações pendentes:
- Validação de `TELEGRAM_BOT_TOKEN` no startup (HTTP 200 em `/getMe`)
- Reconexão automática em falha de rede
- Rate-limiting (~30 msg/s do Telegram API)
- Logs estruturados de envio (msg_id, chat_id, timestamp)

---

## 8. Documentação

`RELATORIO_INCONSISTENCIAS.md` já catalogou 7 críticas + 5 menores, **mas não foram reconciliadas**. Trabalho restante:
- Atualizar números: portais (8 vs 12), testes (149 vs real), versões.
- Adicionar secção macOS no README global (actualmente só Windows).
- Secção **Troubleshooting** com os 3 erros mais comuns: Ollama timeout, Chrome não encontrado, ETL ImportError.
- Eliminar `RELATORIO_INCONSISTENCIAS.md` após reconciliação.

---

## 9. Plano de execução proposto (por ondas)

**Onda 1 — Desbloquear (estimativa: ~3 h)**
1. Fix B1: lazy imports em `enricher.py` + flag `ENRICH_SKIP_HEAVY` honrada.
2. Fix B2: reconciliar `requirements.txt` vs `pyproject.toml` com extras opcionais.
3. Fix B3: `OpportunityAnalyzer` config-driven + warm-up + retry + cache.
4. Smoke test: `start.bat install` → `start.bat doctor` → `start.bat test` → tudo a passar.

**Onda 2 — Paridade e limpeza (~3 h)**
5. Criar `start.sh` raiz com paridade total.
6. Consolidar testes (`tests/` raiz como única) + 2 testes regressão (DetachedInstance + dark mode).
7. Mover `scripts/debug/` para `.gitignore`/produto não-vendido.
8. Limpar `logs/` antigos.

**Onda 3 — UI/Cosmético (~2 h)**
9. CSS global dark-mode em `theme.py`.
10. Auditar 4 tabelas referidas (precisa screenshots/contexto adicional).

**Onda 4 — Robustez 24h + Telegram (~2 h)**
11. Auditar `main_engine.py` + `scheduler/` para loops e leaks.
12. Auditar `notification_engine.py` para reconnect/backoff/rate-limit.

**Onda 5 — Documentação (~2 h)**
13. README global: secção macOS + Troubleshooting + reconciliar números.
14. Eliminar `RELATORIO_INCONSISTENCIAS.md`.
15. Atualizar `realestate_engine/README.md` para apontar a `tests/` na raiz.

**Total estimado: ~12 h de trabalho focado.** Não é fazível numa única passagem sem perder qualidade.

---

## 10. Pendente do utilizador — decisões necessárias

1. **CV/NLP — manter ou cortar?** Se a venda do produto não promete análise de imagens nem NLP avançado, remover totalmente reduz produto em ~3 GB e elimina B1+B2.
2. **Estrutura de testes — escolher uma:** `tests/` raiz (atual) vs `realestate_engine/tests/` (planeada).
3. **Modelo Ollama default — qual?** mistral:7b (atual hardcoded), qwen3-14b-fast (modelfile no projeto), qwen3-35b (modelfile no projeto)?
4. **Limpeza de `scripts/debug/`** — mover para pasta interna ou apagar?

Quando me disseres o que decidir nas 4 questões, executo Onda 1 imediatamente.
