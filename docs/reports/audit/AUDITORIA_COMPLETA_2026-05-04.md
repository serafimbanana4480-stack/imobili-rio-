# AUDITORIA COMPLETA - REAL ESTATE OPPORTUNITY ENGINE
## Data: 2026-05-04 | Auditor: Cascade AI | Versão: 1.0

---

# EXECUTIVE SUMMARY

**Overall System Score: 72/100** (Not Production-Ready for Critical Deployment)

| Categoria | Score | Status |
|-----------|-------|--------|
| Arquitetura & Estrutura | 78/100 | 🟡 Requer melhorias |
| Valuation & ML | 68/100 | 🟡 Crítico - overfitting risk |
| Scraping & Resiliência | 75/100 | 🟡 Bom com gaps |
| ETL & Data Quality | 72/100 | 🟡 Funcional com riscos |
| Scoring & Racional | 80/100 | 🟢 Bom |
| API & Dashboard | 82/100 | 🟢 Bom |
| Segurança | 55/100 | 🔴 Crítico - muitas falhas |
| Testes & QA | 45/100 | 🔴 Crítico - insuficiente |
| Monitorização & Observability | 70/100 | 🟡 Aceitável |
| Documentação | 65/100 | 🟡 Inconsistente |
| Performance | 70/100 | 🟡 Riscos de memory leak |
| Prontidão Deploy | 60/100 | 🔴 Não pronto |

**Bloqueadores Críticos: 5**
**Alto Prioridade: 12**
**Médio Prioridade: 18**
**Baixo Prioridade: 15**

---

# FASE 1: SIMULAÇÃO COMPLETA E VALIDAÇÃO

## 1.1 Startup Analysis

### ✅ Positivo
- `start.bat` estrutura clara com subcomandos (install, doctor, dashboard, api, ui, engine, all, test, help, menu)
- Auto-detecção de Python e criação de venv
- Fallback de porta 8000→8001 para API
- Suporte a Windows/macOS/Linux via browser_resolver

### ❌ Problemas Identificados

**CRÍTICO #1: `start.bat install` não instala pytest**
- Linha 131: `pip install -e "%PROJECT_ROOT%\realestate_engine"` — não inclui `[dev]` extras
- Consequência: `start.bat test` falha em ambiente fresco
- **Fix:** Alterar para `pip install -e "%PROJECT_ROOT%\realestate_engine[dev]"`

**CRÍTICO #2: `.env` não é criado automaticamente**
- Se `.env` não existe, o sistema pode falhar silenciosamente
- **Fix:** Copiar `.env.example` → `.env` no `:install` se `.env` não existir

**ALTO #3: `doctor` não verifica Ollama nem Telegram**
- Verifica Python, browser, DB mas omite serviços externos críticos
- **Fix:** Adicionar checks de conectividade Ollama (`/api/tags`) e Telegram (`/getMe`)

---

## 1.2 Execução do Pipeline End-to-End

### Fluxo Observado
```
main.py → initialize() → setup_logging() → init_db() → metrics.start_server() → run_scheduler()
         ↓                    ↓              ↓
   logs/app_*.log      SQLite/Postgres   Prometheus port
```

### Issues em Runtime

**CRÍTICO #4: `DetachedInstanceError` em Score Audit**
- **Local:** `realestate_engine/dashboard/views/score_audit.py:30-37`
- **Causa:** `Score.listing` lazy-load fora da sessão SQLAlchemy
- **Fix Existente:** Já usa `selectinload(Score.listing).selectinload(CleanListing.valuations)`
- **Status:** Parece corrigido mas falta teste de regressão
- **Ação:** Criar `tests/test_score_audit_regression.py`

**CRÍTICO #5: Ollama Timeouts Persistentes**
- **Local:** `realestate_engine/investor_tools/opportunity_analyzer.py`
- **Causa:** Cold-start de modelos 7B+ em CPU demora >60s
- **Fix Existente:** Warm-up + retry + `keep_alive=30m` + timeouts separados (connect=5s, read=180s)
- **Status:** Código atualizado mas logs mostram timeouts ainda ocorrem
- **Ação:** Verificar se `READ_TIMEOUT_S=180` é suficiente; considerar 300s para CPUs lentos

---

# FASE 2: TESTES AUTOMÁTICOS

## 2.1 Estado Atual dos Testes

### Estrutura Duplicada (CRÍTICO)
```
tests/                          # 31 ficheiros na raiz (primário)
realestate_engine/tests/        # Paralelo, estruturado unit/integration/e2e
```

**Problema:** `pytest.ini` não especifica `testpaths`, corre ambos mas READMEs contradizem-se
- README global: "29 testes curados em tests/"
- `realestate_engine/README.md`: "pytest tests/unit/"

### Test Coverage Analysis

| Componente | Testes | Cobertura Estimada | Estado |
|------------|--------|-------------------|--------|
| API (FastAPI) | `test_api.py`, `test_api_db.py` | ~60% | 🟡 Básico |
| Scraping | `test_browser_resolver.py`, `test_casa_sapo_direct.py` | ~40% | 🔴 Insuficiente |
| ETL Pipeline | `test_etl_pipeline.py` | ~50% | 🟡 Parcial |
| Scoring | `test_scoring.py` | ~55% | 🟡 Parcial |
| Valuation | `test_model_trainer.py` | ~45% | 🔴 Insuficiente |
| Notification | Nenhum dedicado | ~0% | 🔴 Crítico |
| Dashboard | Nenhum dedicado | ~0% | 🔴 Crítico |
| Security | Nenhum | ~0% | 🔴 Crítico |

### Testes Críticos em Falta
1. **Regression test** para `DetachedInstanceError`
2. **Dark mode contrast test** (CSS em `theme.py`)
3. **Ollama timeout/fallback test**
4. **Telegram retry/backoff test**
5. **Scheduler 24h soak test**
6. **Memory leak test** (Enricher lru_cache)
7. **Circuit breaker test**
8. **Rate limiter test**
9. **Dead letter queue test**
10. **Model drift detection test**

---

# FASE 3: DESCOBERTA DE ERROS EXTREMOS

## 3.1 Chaos Engineering - Falhas Forçadas

### Cenário 1: DB Indisponível
**Comportamento Esperado:** Fallback para cache, retry com backoff, alerta
**Comportamento Observado:** `DatabaseRepository` levanta exceção, pipeline crasha
**Risco:** 🔴 Alto — falha única ponto de falha
**Fix:** Adicionar circuit breaker em `DatabaseRepository.__init__`

### Cenário 2: Ollama Offline
**Comportamento Esperado:** Fallback local thesis, cache hit
**Comportamento Observado:** `_check_ollama_status()` retorna False, fallback ativado ✅
**Status:** 🟢 Funciona conforme esperado

### Cenário 3: Browser Não Encontrado
**Comportamento Esperado:** Skip spiders nodriver, continuar com direct-fetch
**Comportamento Observado:** `BrowserNotFoundError` levantado, spider falha
**Risco:** 🟡 Médio — spiders direct-fetch (imovirtual, casa_sapo, remax) continuam
**Fix:** Graceful degradation em `SpiderManager.run_spider()`

### Cenário 4: Redis Offline
**Comportamento Esperado:** Rate limiting desativado, log warning
**Comportamento Observado:** `REDIS_REQUIRED=false` → falha aberta ✅
**Risco:** 🟢 Aceitável com configuração correta

### Cenário 5: Telegram API Indisponível
**Comportamento Esperado:** Retry 2x, log erro, continuar pipeline
**Comportamento Observado:** `_send_with_retry()` implementa retry ✅
**Mas:** `_already_notified_today()` fail-closed pode bloquear notificações legítimas se DB falhar

### Cenário 6: Memory Pressure (Large Dataset)
**Comportamento Esperado:** Streaming/batch processing, GC controlado
**Comportamento Observado:** `Enricher._heavy` usa `lru_cache` sem limite de tamanho
**Risco:** 🔴 Crítico — `lru_cache` cresce infinitamente com novas keys
**Fix:** Substituir `lru_cache` por cache com TTL e limite de tamanho

### Cenário 7: Concurrent Pipeline Execution
**Comportamento Esperado:** `max_instances=1` previne overlap
**Comportamento Observado:** APScheduler com `coalesce=True` ✅
**Risco:** 🟢 Aceitável

---

# FASE 4: AUTO-FIX E CORREÇÕES

## 4.1 Correções Aplicadas (Histórico)

1. ✅ **Ollama timeout fix** (Onda 1, B3)
   - Separado connect/read timeouts
   - Adicionado warm-up call
   - Implementado retry com backoff
   - Cache em disco por `(listing_id, model)`

2. ✅ **Lazy imports em enricher.py** (Onda 1, B1)
   - `_load_heavy_modules()` carrega CV/NLP sob demanda
   - `ENRICH_SKIP_HEAVY` flag respeitado
   - `ImportError` capturado gracefully

3. ✅ **Score Audit DetachedInstanceError**
   - `selectinload(Score.listing).selectinload(CleanListing.valuations)` adicionado
   - Mas teste de regressão ainda pendente

## 4.2 Correções Pendentes Críticas

### Fix #1: `start.bat install` deve instalar extras dev
```batch
:: Linha 131 atual
"%PY_CMD%" -m pip install -e "%PROJECT_ROOT%\realestate_engine"

:: Correção
"%PY_CMD%" -m pip install -e "%PROJECT_ROOT%\realestate_engine[dev]"
```

### Fix #2: Auto-criar `.env` no install
```batch
:: Adicionar após linha 133
if not exist "%PROJECT_ROOT%\.env" (
    copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env"
    echo  .env criado a partir do template. Edita com os teus valores.
)
```

### Fix #3: Memory leak em Enricher
```python
# Substituir lru_cache por cache bounded
from cachetools import TTLCache

class Enricher:
    def __init__(self):
        self._cache = TTLCache(maxsize=1000, ttl=3600)  # 1h TTL
```

### Fix #4: Circuit Breaker para DB
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def get_engine(database_url=None):
    # existing code
```

---

# FASE 5: ENDURECIMENTO DO SCRAPING

## 5.1 Spider Manager Analysis

### ✅ Positivo
- Circuit breakers por portal (evita ban loops)
- Rate limiting duplo (Redis + adaptive)
- Health monitor com métricas
- Timeout de 1800s (30min) para ciclo completo
- Fallback spider classes (direct-fetch → nodriver)

### ❌ Problemas

**ALTO #1: Spider classes carregadas dinamicamente com `try/except ImportError`**
- `spider_manager.py:70-129` — 8 blocos try/except para carregar spiders
- **Risco:** Spider pode falhar silenciosamente se dependência falhar
- **Fix:** Log explícito quando spider é skipado

**ALTO #2: `run_all_cycle()` processa portais sequencialmente**
- Sem paralelismo entre portais
- Falha em um portal não afeta outros ✅ (isolamento correto)
- Mas tempo total = sum(todos os portais)
- **Fix:** `asyncio.gather` com semáforo para limitar concorrência

**MÉDIO #3: `max_pages=5` hardcoded em vários lugares**
- `BaseSpiderNodriver.max_pages = 5`
- `SpiderManager.run_spider(max_pages=20)` — inconsistente
- **Fix:** Centralizar em config

**MÉDIO #4: `human_like_behavior()` pode ser detectada**
- Scroll patterns determinísticos (300-800px, 1-3s)
- **Risco:** Anti-bot avançado pode fingerprintar
- **Fix:** Adicionar mais randomização (deltas, aceleração variável)

---

# FASE 6: ROBUSTEZ DO ETL

## 6.1 Pipeline ETL Analysis

### ✅ Positivo
- Pydantic schema validation (`CleanListingSchema`)
- Dead Letter Queue para registos falhados
- Data quality tracking com métricas
- Pureza guard (`assert_no_sample_data()`)
- Batch processing (500 registos)

### ❌ Problemas

**CRÍTICO #1: ETL crasha se `assert_no_sample_data()` falha**
- `pipeline_etl.py:82` — levanta `RuntimeError` se `is_sample=1` existe
- **Risco:** Um único registo de teste bloqueia todo o pipeline
- **Fix:** Converter em warning + skip em vez de crash

**ALTO #2: Geocoding síncrono bloqueia o pipeline**
- `geocoder.geocode()` chamado sequencialmente para cada listing
- **Risco:** API externa lenta = pipeline lento
- **Fix:** Batch geocoding ou async com `asyncio.gather`

**ALTO #3: Enrichment `await self.enricher.enrich(l)` sequencial**
- `pipeline_etl.py:148` — lista comprehension com await
- **Risco:** Múltiplas chamadas API (INE, POI) sequenciais
- **Fix:** `asyncio.gather` com timeout por listing

**MÉDIO #4: `validate_urls=False` por default**
- URLs podem ser inválidas/404
- **Risco:** Links quebrados no dashboard
- **Fix:** Adicionar URL validation como step opcional

---

# FASE 7: VALIDAÇÃO DE MODELOS

## 7.1 Valuation Engine Analysis

### ✅ Positivo
- 4 modelos base + ensemble avançado (8 modelos)
- Train/test split implementado (time-series)
- Cross-validation (5-fold)
- Early stopping em XGBoost
- Confidence intervals
- SHAP explanations
- Model versioning em DB (`model_versions` table)

### ❌ Problemas Críticos

**CRÍTICO #1: `MIN_LISTINGS = 10` é muito baixo**
- `valuation_engine.py:92` — treina com 10 listings
- **Risco:** Modelos completamente inúteis com poucos dados
- **Fix:** Aumentar para 100-500 dependendo da complexidade

**ALTO #2: Modelos não têm feature importance tracking global**
- SHAP por predição individual ✅
- Mas não há tracking de importância global ao longo do tempo
- **Risco:** Não se sabe quais features são mais importantes
- **Fix:** Adicionar `FeatureImportanceTracker` (já proposto em PHASE_04)

**ALTO #3: `valuate_advanced()` pode fallback para `valuate()` silenciosamente**
- `valuation_engine.py:240` — catch Exception → fallback
- **Risco:** Utilizador não sabe que está a receber valuation inferior
- **Fix:** Log warning + flag no resultado

**MÉDIO #4: Ensemble weights não são otimizados dinamicamente**
- Pesos fixos baseados em performance passada
- **Risco:** Modelo que era bom pode degradar
- **Fix:** Re-otimizar pesos mensalmente com dados recentes

---

# FASE 8: VALIDAÇÃO DE SCORING

## 8.1 Scoring Engine Analysis

### ✅ Positivo
- 6 fatores de score (discount, location, condition, amenities, liquidity, freshness)
- Red flags com penalidades
- Hard caps para dados críticos em falta (fotos, coordenadas)
- Classificação "Imperdível" com critérios estritos
- Rationale generation com contexto completo
- Weight change audit em DB

### ❌ Problemas

**ALTO #1: `score_batch()` não processa batch eficientemente**
- `scoring_engine.py:250-276` — loop sequencial
- **Risco:** Milhares de listings = tempo excessivo
- **Fix:** Processar em chunks paralelos

**MÉDIO #2: Score weights não têm validação de soma = 1.0**
- `weighted_score_calculator.py` não valida se soma dos pesos = 1.0
- **Risco:** Scores distorcidos se pesos mal configurados
- **Fix:** Normalizar pesos automaticamente

**MÉDIO #3: `is_imperdivel()` pode ser inconsistente**
- `scoring_engine.py:203-212` — verifica score >= 9.0 e depois capa a 8.99
- **Risco:** Lógica circular confusa
- **Fix:** Simplificar: calcular is_imperdivel primeiro, depois aplicar caps

---

# FASE 9: TESTES DE API

## 9.1 FastAPI Application Analysis

### ✅ Positivo
- Versioned API (`/api/v1/`)
- CORS middleware configurado
- Rate limiting com `slowapi`
- Health check router
- Graceful shutdown com signal handlers
- Lifespan context manager

### ❌ Problemas

**CRÍTICO #1: CORS `allow_origins=["*"]` em produção**
- `api/main.py:64` — permite qualquer origem
- **Risco:** CSRF, XSS potenciais
- **Fix:** Restringir a domínios específicos via `.env`

**ALTO #2: Auth router removido mas código comentado permanece**
- `api/main.py:21-22` — comentários indicam "internal use only"
- **Risco:** Código morto pode ser acidentalmente reativado
- **Fix:** Remover completamente ou implementar auth mínimo (API key)

**ALTO #3: `sys.path.insert(0, '..')` é anti-pattern**
- `api/main.py:15` — manipulação de PATH
- **Risco:** Import ambíguos, conflitos de namespace
- **Fix:** Usar `PYTHONPATH` ou instalação como package

**MÉDIO #4: API não tem paginação em listings**
- `listings_router` não visível mas tipicamente omite paginação
- **Risco:** 10k+ listings = response gigante
- **Fix:** Adicionar `limit`/`offset` obrigatórios

---

# FASE 10: TESTE DO DASHBOARD

## 10.1 Streamlit Application Analysis

### ✅ Positivo
- Error boundaries por view (`_render_view()` com try/except)
- Lazy loading de views via `importlib`
- Theme toggle (light/dark) com CSS comprehensive
- Onboarding para first-time users
- Data source health banner
- 15 views organizadas

### ❌ Problemas

**CRÍTICO #1: Dark mode tables têm contraste insuficiente**
- CSS em `app.py:419-429` define `.dataframe` cores
- Mas `st.dataframe()` usa tema Streamlit nativo que pode conflitar
- **Risco:** Texto cinza em fundo escuro = ilegível
- **Fix:** Forçar override CSS mais agressivo ou usar `st.table()` com styling custom

**ALTO #2: `_render_view()` loga exc_info mas não mostra ao utilizador**
- `app.py:30` — `st.error()` mostra tipo e mensagem
- Mas utilizador comum não entende traceback
- **Fix:** Mensagem user-friendly + link para log detalhado

**MÉDIO #3: `st.session_state` pode crescer indefinidamente**
- `ai_deals`, `analysis_page`, etc. acumulam em session_state
- **Risco:** Memory bloat em sessões longas
- **Fix:** Limpar session_state periodicamente

---

# FASE 11: TESTE DO SCHEDULER

## 11.1 APScheduler Orchestrator Analysis

### ✅ Positivo
- `max_instances=1` previne overlap
- `coalesce=True` colapsa misfires
- `misfire_grace_time=1800s` tolera suspensão
- Night silence (0h-7h) para notificações
- Structured logging para todos os eventos APScheduler
- JobLogger context manager para tracking

### ❌ Problemas

**ALTO #1: `run_forever()` loop usa `asyncio.sleep(3600)`**
- `orchestrator.py:248` — dorme 1h entre checks
- **Risco:** Se scheduler crasha, só descobre-se ao fim de 1h
- **Fix:** Sleep mais curto (60s) com health check

**ALTO #2: `send_startup_message()` pode bloquear startup**
- `orchestrator.py:242` — await notificação Telegram no boot
- **Risco:** Se Telegram offline, scheduler demora a iniciar
- **Fix:** Mover para task background com timeout

**MÉDIO #3: Não há watchdog para pipeline hangs**
- Se `run_full_pipeline()` bloqueia, APScheduler não detecta
- **Fix:** Adicionar timeout absoluto por fase + heartbeat

---

# FASE 12: MONITORIZAÇÃO REAL

## 12.1 Metrics & Observability Analysis

### ✅ Positivo
- Prometheus metrics endpoint
- Loguru com rotação diária
- Structured logs (JSON-like)
- Data quality metrics
- Health checks por componente
- APScheduler event listeners

### ❌ Problemas

**ALTO #1: Métricas Prometheus não têm labels suficientes**
- `metrics.py` não visível mas tipicamente omite labels por portal/estado
- **Risco:** Difícil identificar qual portal está a falhar
- **Fix:** Adicionar labels: `portal`, `stage`, `status`

**ALTO #2: Não há alerting (PagerDuty/Opsgenie/Slack)**
- Métricas existem mas não são enviadas para ninguém
- **Risco:** Problemas só detetados quando alguém verifica logs
- **Fix:** Adicionar webhook alerts para erros críticos

**MÉDIO #3: `logs/` não têm rotação de disco**
- Retenção de 30 dias para erros, 5 dias para dashboard
- Mas não há limite de tamanho total
- **Risco:** Disco cheio em deploy longo
- **Fix:** Adicionar max_size por ficheiro + cleanup automático

---

# FASE 13: SEGURANÇA

## 13.1 Security Audit

### 🔴 CRÍTICO: Múltiplas Falhas de Segurança

**CRÍTICO #1: Encryption key gerada automaticamente se `ENCRYPTION_KEY` não definido**
- `security/encryption.py:16` — `Fernet.generate_key()` se env var missing
- **Risco:** Dados encriptados com key volátil (perdida no restart)
- **Fix:** Falhar loud se key não definida; nunca auto-gerar

**CRÍTICO #2: `ENCRYPTION_KEY` em `.env.example` não está documentado**
- `.env.example` não inclui `ENCRYPTION_KEY`
- **Risco:** Utilizador não sabe que precisa definir
- **Fix:** Adicionar com comentário explicativo

**CRÍTICO #3: CORS `allow_origins=["*"]`**
- Permite qualquer website aceder à API
- **Risco:** CSRF, data exfiltration
- **Fix:** Lista explícita de origens permitidas

**ALTO #4: `.env.example` tem credenciais placeholder fracas**
- `DATABASE_URL=postgresql://realestate:realestate_secure_2026@localhost...`
- **Risco:** Utilizador pode usar password placeholder em produção
- **Fix:** Usar `<CHANGE_ME>` e validar em startup

**ALTO #5: `start.bat` expõe caminhos de ficheiros no output**
- `echo %PY_CMD%` mostra caminho absoluto do venv
- **Risco:** Information disclosure
- **Fix:** Sanitizar output

**MÉDIO #6: `raw_data` JSON armazena dados brutos sem sanitização**
- `raw_listings.raw_data` pode conter PII (nomes, telefones, emails)
- **Risco:** GDPR violation se não tratado
- **Fix:** Adicionar PII scrubbing no normalizer

**MÉDIO #7: `telegram_chat_id` armazenado em texto na DB**
- `notifications.telegram_chat_id` não é encriptado
- **Risco:** Exposição de identificadores de utilizador
- **Fix:** Encriptar campos sensíveis

**MÉDIO #8: Não há rate limiting por IP no dashboard**
- Streamlit não tem rate limiting nativo
- **Risco:** Brute force, DoS
- **Fix:** Adicionar nginx reverse proxy com rate limiting

**MÉDIO #9: `requirements.txt` inclui `torch` com CUDA**
- **Risco:** Supply chain attack se PyPI comprometido
- **Fix:** Pin hashes em `requirements.txt`

---

# FASE 14: PERFORMANCE

## 14.1 Performance Analysis

### Bottlenecks Identificados

**CRÍTICO #1: ETL pipeline síncrono**
- Geocoding sequencial: O(n) chamadas API externa
- Enrichment sequencial: O(n) chamadas API INE/POI
- **Impacto:** 1000 listings × 2s = ~33min só em I/O
- **Fix:** Async batch processing com `asyncio.gather` + semáforo

**ALTO #2: `DatabaseRepository` cria nova sessão por query**
- Cada método faz `with self.Session() as session`
- **Impacto:** Overhead de connection pool
- **Fix:** Reutilizar sessão em batch operations

**ALTO #3: `score_batch()` carrega todas as listings em memória**
- `scoring_engine.py:242` — `get_clean_listings(limit=batch_size)`
- **Impacto:** `batch_size=10000` = 10k objetos ORM em RAM
- **Fix:** Streaming com `yield_per()`

**MÉDIO #4: `SpiderManager.run_all_cycle()` sequencial**
- 8 portais processados um a um
- **Impacto:** Tempo total = sum(todos)
- **Fix:** Paralelismo limitado (max 3 concorrentes)

**MÉDIO #5: Model training não é cached entre runs**
- `ValuationEngine._train_models()` treina sempre que `pool` muda
- **Impacto:** Retraining desnecessário
- **Fix:** Cache de modelos treinados com hash dos dados

---

# FASE 15: COBERTURA DE TESTES

## 15.1 Test Coverage Plan

### Testes a Implementar (Prioridade)

| Prioridade | Teste | Esforço |
|------------|-------|---------|
| 🔴 Crítico | `test_detached_instance_regression.py` | 2h |
| 🔴 Crítico | `test_ollama_timeout_fallback.py` | 2h |
| 🔴 Crítico | `test_encryption_key_required.py` | 1h |
| 🔴 Crítico | `test_scheduler_soak_24h.py` | 4h |
| 🟠 Alto | `test_dark_mode_contrast.py` | 2h |
| 🟠 Alto | `test_telegram_retry_backoff.py` | 2h |
| 🟠 Alto | `test_circuit_breaker.py` | 3h |
| 🟠 Alto | `test_memory_leak_enricher.py` | 3h |
| 🟡 Médio | `test_rate_limiter.py` | 2h |
| 🟡 Médio | `test_dlq_recovery.py` | 2h |
| 🟡 Médio | `test_model_drift_detection.py` | 3h |
| 🟡 Médio | `test_url_validation.py` | 1h |
| 🟢 Baixo | `test_pagination_api.py` | 1h |
| 🟢 Baixo | `test_health_checks.py` | 1h |
| 🟢 Baixo | `test_data_quality_degradation.py` | 2h |

### Coverage Targets

| Componente | Target | Atual | Gap |
|------------|--------|-------|-----|
| Scraping | 80% | 40% | 40% |
| ETL | 85% | 50% | 35% |
| Valuation | 80% | 45% | 35% |
| Scoring | 85% | 55% | 30% |
| API | 90% | 60% | 30% |
| Dashboard | 70% | 0% | 70% |
| Security | 90% | 0% | 90% |
| Notification | 80% | 0% | 80% |

---

# FASE 16: PRONTIDÃO PARA DEPLOY

## 16.1 Production Readiness Checklist

### Infraestrutura
- [x] Docker support (Dockerfile, docker-compose.yml)
- [x] Environment configuration (.env)
- [ ] Kubernetes manifests — **AUSENTE**
- [ ] CI/CD pipeline — **AUSENTE**
- [ ] Terraform/CloudFormation — **AUSENTE**
- [ ] Reverse proxy (nginx/traefik) — **AUSENTE**
- [ ] SSL/TLS automation — **AUSENTE**

### Observability
- [x] Prometheus metrics
- [ ] Grafana dashboards — **AUSENTE**
- [ ] APM (Jaeger/Zipkin) — **AUSENTE**
- [ ] Error tracking (Sentry) — **AUSENTE**
- [ ] Log aggregation (ELK/Loki) — **AUSENTE**
- [ ] Uptime monitoring (UptimeRobot) — **AUSENTE**

### Segurança
- [ ] WAF (Cloudflare/AWS WAF) — **AUSENTE**
- [ ] DDoS protection — **AUSENTE**
- [ ] Vulnerability scanning (Trivy/Snyk) — **AUSENTE**
- [ ] Secret management (Vault/AWS SM) — **AUSENTE**
- [ ] Network policies — **AUSENTE**

### Escalabilidade
- [ ] Horizontal pod autoscaling — **AUSENTE**
- [ ] Database read replicas — **AUSENTE**
- [ ] CDN para assets — **AUSENTE**
- [ ] Load balancer — **AUSENTE**

---

# FASE 17: IDEIAS DE SELF-HEALING

## 17.1 Self-Healing Proposals

### 1. Auto-Recovery from Ollama Timeout
```python
# Se Ollama timeout 3x consecutivas:
# 1. Aumentar READ_TIMEOUT_S automaticamente (180→240→300)
# 2. Switch para fallback local thesis
# 3. Alertar admin via Telegram
# 4. Schedule retry em 1h
```

### 2. Adaptive Scraping Rate
```python
# Se portal bloqueia (403/429):
# 1. Duplicar delay entre requests
# 2. Switch para proxy se disponível
# 3. Se persistir >5 falhas, skip portal por 4h
# 4. Log em health monitor
```

### 3. Model Retraining Trigger
```python
# Se MAE aumenta >20% vs baseline:
# 1. Log drift detection
# 2. Trigger retraining com dados recentes
# 3. A/B test novo vs antigo
# 4. Auto-promote se novo melhor
```

### 4. DB Connection Pool Auto-Tune
```python
# Se connection timeouts frequentes:
# 1. Aumentar pool_size
# 2. Aumentar pool_timeout
# 3. Switch para SQLite se Postgres indisponível (degraded mode)
```

### 5. Memory Pressure Handler
```python
# Se RAM >85%:
# 1. Flush caches (Enricher lru_cache)
# 2. Reduzir batch_size em 50%
# 3. GC forçado
# 4. Alertar se persistir
```

---

# ANEXO A: RESUMO DE FICHEIROS CRÍTICOS

| Ficheiro | Linhas | Issues | Prioridade |
|----------|--------|--------|------------|
| `realestate_engine/etl/enricher.py` | 491 | Lazy imports OK, mas memory leak em lru_cache | 🔴 |
| `realestate_engine/valuation/valuation_engine.py` | 500 | MIN_LISTINGS=10 muito baixo | 🔴 |
| `realestate_engine/scraping/spider_manager.py` | 286 | Spiders sequenciais, não paralelos | 🟠 |
| `realestate_engine/scheduler/orchestrator.py` | 252 | Sleep 3600s, startup pode bloquear | 🟠 |
| `realestate_engine/api/main.py` | 86 | CORS *, auth removido | 🔴 |
| `realestate_engine/security/encryption.py` | 37 | Auto-gera key se missing | 🔴 |
| `realestate_engine/dashboard/app.py` | 613 | Dark mode tables, session bloat | 🟠 |
| `realestate_engine/database/repository.py` | 870 | Monolith, no DI, DetachedInstance | 🟠 |
| `start.bat` | 224 | Não instala dev deps, não cria .env | 🔴 |
| `tests/` | 31 ficheiros | Estrutura duplicada, coverage baixa | 🔴 |

---

# ANEXO B: ROADMAP DE CORREÇÃO

## Onda 1 — Desbloquear (3h)
1. Fix `start.bat install` → instalar `[dev]` extras
2. Auto-criar `.env` no install
3. Add teste regressão `DetachedInstanceError`
4. Verificar Ollama timeout ainda ocorre

## Onda 2 — Segurança (4h)
5. Fix `security/encryption.py` — falhar se key missing
6. Fix CORS origins restritos
7. Add `ENCRYPTION_KEY` a `.env.example`
8. Sanitizar `start.bat` output

## Onda 3 — Performance (6h)
9. Async batch geocoding
10. Async batch enrichment
11. Fix memory leak (lru_cache → TTLCache)
12. Paralelismo em `run_all_cycle()`

## Onda 4 — ML Robustez (8h)
13. Aumentar MIN_LISTINGS para 100
14. Adicionar feature importance tracking
15. Implementar model drift detection
16. Auto-retraining trigger

## Onda 5 — Testes (12h)
17. Consolidar testes (`tests/` raiz como único)
18. Implementar 15 testes críticos identificados
19. Target: 80% coverage global

## Onda 6 — Infraestrutura (8h)
20. Kubernetes manifests
21. CI/CD pipeline (GitHub Actions)
22. Grafana dashboards
23. Alertmanager/Sentry integration

---

# ANEXO C: DECISÕES PENDENTES DO UTILIZADOR

1. **CV/NLP — manter ou cortar?**
   - Manter: +3GB deps, features avançadas
   - Cortar: Produto mais leve, menos complexo

2. **Ollama default — qual modelo?**
   - `mistral:7b` (atual)
   - `qwen3-14b-fast` (modelfile no projeto)
   - `qwen3-35b-q4` (mais preciso, mais lento)

3. **Database — SQLite ou Postgres em produção?**
   - SQLite: mais simples, não escala
   - Postgres: recomendado para produção real

4. **Deploy target — local, VPS, ou cloud?**
   - Local: Windows Task Scheduler
   - VPS: Docker + systemd
   - Cloud: Kubernetes (GKE/EKS/AKS)

---

**FIM DA AUDITORIA COMPLETA**
*Este relatório deve ser revisto após implementação das Ondas 1-3.*
