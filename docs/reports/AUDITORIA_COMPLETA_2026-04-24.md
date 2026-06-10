# Relatorio Auditoria — RealEstate Engine
**Data:** 2026-04-24 | **Runtime:** Python 3.14.3 | **BD:** SQLite `data/db/realestate.db`

---

## 1. Resumo Executivo
Veredicto: **NOT READY**. O pipeline funciona apenas para Imovirtual (2.751 raw → 1.375 clean → 1.375 valuations → 1.375 scores). Ha perda de 50 % no ETL, geocodificacao inexistente em 91 % dos imoveis, 7 de 8 spiders inoperacionais, notificacoes desativadas, scheduler nao a correr como daemon e 1 teste unitario falhado. Estimativa: 2–4 semanas para production-readiness.

| Severidade | Qtd |
|------------|-----|
| Critico    | 4   |
| Alto       | 6   |
| Medio      | 7   |
| Baixo      | 5   |

---

## 2. Estrutura do Projeto
Todos os modulos existem: scraping (10 spiders), ETL (6 componentes), valuation (8 modelos), scoring (5 calculators + red flags + rationale), database (SQLAlchemy), dashboard (13 views), notification (4 componentes), scheduler (orchestrator + 5 jobs), monitoring, security, NLP, CV, quality 5D.
Inconsistencias: `requirements-dev.txt` ausente (referenciado no CI); `test_results.txt` na raiz (UTF-16 BOM) provoca erro no pytest collection.

---

## 3. Dependencias e Ambiente
- Runtime Python 3.14.3 diverge do CI (3.10–3.12) e do Dockerfile (`python:3.10-slim`).
- Warnings criticos: Pydantic V1 incompatibility com Python 3.14+; `asyncio.iscoroutinefunction` deprecado.
- Servicos: Redis indisponivel; PostgreSQL nao migrado; Prometheus/Grafana configurados mas offline.

---

## 4. Base de Dados
| Tabela | Registros | Observacao |
|--------|-----------|------------|
| raw_listings | 2.751 | 100 % imovirtual, 0 sample |
| clean_listings | 1.375 | Perda ~50 % ETL |
| valuations | 1.375 | 1:1 com clean |
| scores | 1.375 | 1:1 com clean |
| price_history | 0 | Tracking inativo |
| notifications | 0 | Nunca enviadas |
| watchlist | 0 | Nao utilizada |
| job_execution_log | 9 | Apenas scraping manual |
| ine_data | 0 | Dados macro ausentes |
| geocoding_cache | 21 | Cache minimo |
| system_metrics | 0 | Sem metricas |
| config | 0 | Sem entradas |

Qualidade: `lat/lon` NULL em **1.255 / 1.375 (91,3 %)** — critico. `preco_por_m2`, `quartos`, `area_util_m2` com 0 NULL (OK). Preco maximo 6.000.000 EUR (suspeito). Foreign keys: 0 violations (OK). Ultimos dados: 2026-04-24.

---

## 5. Scraping Layer
| Portal | Tecnologia | Estado | Resultado |
|--------|------------|--------|-----------|
| Imovirtual | httpx + __NEXT_DATA__ | Funcional | 2.751 listings |
| Idealista | nodriver | Bloqueado | Requer proxy |
| Casa Sapo | nodriver | Falha | 1.486 extraidos mas ETL insere 0 |
| ERA | nodriver | Falha | 0 listings (seletores nao encontram) |
| REMAX/OLX/Century21/SuperCasa | nodriver | Bloqueados | Requer proxy |

Problemas: proxy ausente; ERA sem seletores atualizados; Casa Sapo bloqueado pelo bug ETL coroutine; ERASpider falha com `'ERASpider' object has no attribute 'scroll_page'` (errors.log).

---

## 6. ETL Layer
**Perda 50 % (2.751 → 1.375):** deduplicacao intra-portal (overlap paginas Imovirtual) + sem lat/lon (91 % NULL) → deduplicator recorre a `source_disambig = f"{source_portal}_{source_id}"`. Se `source_id` for vazio/instavel, listings distintos colidem. Buckets: area ±5 m2, preco ±5.000 EUR, geo ~100 m — agressivo para zonas densas.

**Bug critico — Coroutine no Enricher (errors.log 2026-04-22):**
```
TypeError: float() argument must be a string or a real number, not 'coroutine'
SQL: INSERT INTO clean_listings ...
```
O enricher chama metodos async (ex: `POIClient.get_nearest_distance`) sem `await`. O `_sanitize_value` no `pipeline_etl.py` cobre campos explicitos mas nao todos os dinamicos. Explica por que Casa Sapo gera 0 clean listings enquanto Imovirtual insere 1.375.

---

## 7. Valuation Engine
Modelos implementados: Hedonic (Huber), XGBoost, Comparaveis, INE Client, Weighted Ensemble, Confidence Interval, Advanced Ensemble (8 modelos). SHAP integrado. INE Client com dados vazios (`ine_data` = 0). Todos os 1.375 clean listings tem valuation e score, indicando que o engine gera estimativas via fallback/heuristicas quando modelos nao estao treinados.

---

## 8. Scoring Engine
Todos os componentes existem e funcionam: discount (45 %), location (20 %), condition (15 %), liquidity (10 %), freshness (10 %), red_flags_detector, rationale_generator, weighted_score_calculator. 1.375 scores gerados. Classificacao `Imperdivel` protegida contra red flags criticos.

---

## 9. Dashboard
13 views: overview, search, watchlist, market_analysis, investor_tools, telegram, config, system, scraping_results, map_view, pipeline_status, data_quality_dashboard, debug_logs. Map view degradado (91 % sem coordenadas). Sem autenticacao.

---

## 10. Scheduler
Orchestrator com AsyncIOScheduler e 2 jobs (full pipeline hourly 08:00–22:00, daily summary 20:30). Circuit breakers implementados. Job execution log com apenas 9 registros manuais — nenhum de ETL, valuation, scoring ou notifications. Causa: scheduler nunca iniciado como daemon (`run_forever()` nao invocado automaticamente).

---

## 11. Notification Engine
Componentes implementados. Telegram bot usa `python-telegram-bot>=20.7`. `.env` tem token placeholder → `_bot` None → notificacoes skipped. Tabela `notifications` = 0.

---

## 12. Monitoring e Logging
Logs: `engine.log` (26.895 linhas, ativo), `errors.log` (666 linhas, erros ETL/spiders). Health checks implementados (DB, Redis, External APIs, Disk/Memory). Alert Manager existe mas sem triggers.

---

## 13. Testes
299 testes identificados. Execucao unit: **158 passed, 1 failed, 39 warnings**.

Falha: `tests/unit/test_pipeline_etl.py::test_deduplicator_integration`
Causa: teste usa 2 listings (area 100 vs 102, preco 300k vs 302k). Deduplicator arredonda area para 100 e preco para 300k. Como geo_bucket = `NoGeo`, usa `source_disambig = f"{source_portal}_{source_id}"`. Portais/IDs diferentes → fingerprint diferente → teste espera 1 mas obtem 2.

Erro de collection: `test_results.txt` na raiz (UTF-16 LE BOM `\xff\xfe`) provoca `UnicodeDecodeError` no pytest.

---

## 14. Documentacao
README.md completo. docs/PROJECT_STRUCTURE.md e docs/README.md existem. planeamento/ com 20 ficheiros. .gsd/REQUIREMENTS.md e ROADMAP.md presentes. Docstrings nas classes principais.

---

## 15. Infraestrutura e Deployment
Docker Compose: PostgreSQL 16, Redis 7, Prometheus, Grafana. Dockerfile: `python:3.10-slim` (diverge). CI/CD: `.github/workflows/ci.yml` com testes 3.10–3.12, linting, coverage, bandit. Scripts `start_scheduler.bat`, `start_system.bat`, `start_dashboard.bat` existem. Falta: `requirements-dev.txt`.

---

## 16. Seguranca
`.env` no `.gitignore`. Credenciais sao placeholders. SecretsManager e EncryptionManager usam env vars. Nenhuma credencial hardcoded encontrada. Docker Compose tem password hardcoded `realestate_secure_2026` (aceitavel para dev). Dashboard sem autenticacao. Sem rate limiting.

---

## 17. Performance
Testes de performance e benchmarks ausentes. Redis indisponivel; geocoding cache com 21 entradas. Indices SQLAlchemy configurados em todas as tabelas. Lazy loading nao avaliado.

---

## 18. Requisitos Nao Implementados
- INE API real (R1.3.1) — `ine_data` vazio.
- Weekly INE refresh (R1.3.2) — nao funcional.
- OHE Freguesias (R1.4.1) — nao confirmado.
- Distance to Center (R2.1.2) — nao visto.
- ROI / Cash Flow (R2.2.1) — pendente.
- Side-by-side Comparison (R3.1.1) — nao encontrado.
- PDF Export (R3.2.2) — nao encontrado.
- 95 % anti-bot success (NF4.1) — nao atingido (apenas 1/8 portais).

---

## 19. Production Readiness Checklist
- Scraping: Parcial (1/8 portais) 🔴
- ETL: Parcial (50 % loss + coroutine bug) 🔴
- Valuation: Funcional (fallbacks) 🟡
- Scoring: Sim ✅
- Dashboard: Parcial (sem coordenadas) 🟡
- Notificacoes: Nao ❌
- Scheduler: Nao ❌
- Monitoring: Parcial 🟡
- Health checks: Sim ✅
- Backup: Nao ❌
- Error handling: Sim ✅
- Security: Parcial (sem auth) 🟡
- Performance: Nao ❌
- Testes: Parcial (1 falha) 🟡
- Documentacao: Sim ✅
- CI/CD: Sim ✅
- Deployment: Parcial 🟡

---

## 20. Recomendacoes Prioritarias (Top 10)
1. **Corrigir ETL coroutine bug** — enricher retorna coroutine nao awaited. Impacto: ETL falha para spiders nodriver. Esforco: 2–4h.
2. **Ativar proxy residencial** — sem proxy, 7 portais bloqueados. Esforco: configuracao + custo.
3. **Corrigir geocodificacao** — 91 % sem lat/lon. Impacto: map, location scoring, dedup degradados. Esforco: 1–2 dias (multi-provider fallback).
4. **Configurar Telegram** — inserir token/chat_id reais no `.env`. Esforco: 30 min.
5. **Iniciar scheduler como daemon** — `start_scheduler.bat` ou servico Windows/systemd. Esforco: 2–4h.
6. **Migrar para PostgreSQL** — SQLite nao suporta concorrencia de escritas. Esforco: 1 dia (docker-compose pronto).
7. **Diagnosticar deduplicacao** — revisar buckets (5 m2 / 5.000 EUR) e logica `source_disambig`. Esforco: 1 dia.
8. **Corrigir teste unitario falhado** — ajustar expectativa do teste ou logica de dedup cross-portal. Esforco: 1h.
9. **Atualizar seletores ERA/Casa Sapo** — paginas requerem hydration diferente. Esforco: 1–2 dias cada.
10. **Migrar para Python 3.10–3.12** — runtime 3.14 gera incompatibilidades Pydantic. Esforco: 1 dia.

---

## 21. Conclusao
O projeto tem arquitetura solida e codigo bem estruturado, mas **nao esta pronto para producao**.
Blockers criticos: (1) bug ETL coroutine que impede processamento de 7 portais; (2) 91 % dos dados sem coordenadas; (3) dependencia total de um unico spider; (4) scheduler e notificacoes inativos.
Proximos passos recomendados: corrigir o coroutine bug, configurar proxy, migrar para PostgreSQL e iniciar o scheduler como servico. Com estas correcoes, o sistema pode atingir production-readiness em 2–4 semanas.
