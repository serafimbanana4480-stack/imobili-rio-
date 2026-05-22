# PROMPT — Auditoria Completa e Verificação de Production-Readiness do RealEstate Engine

## 🎯 INSTRUÇÕES CRÍTICAS PARA A IA

**ATENÇÃO ABSOLUTA:**
- **NÃO FAÇAS NENHUMA ALTERAÇÃO** no código, ficheiros, base de dados ou configurações do projeto
- **NÃO EXECUTES** comandos que modifiquem o estado do sistema (DELETE, DROP, UPDATE, INSERT, etc.)
- **NÃO INSTALES** novos pacotes ou dependências
- **NÃO MODIFIQUES** ficheiros de configuração (.env, configs/, etc.)
- **APENAS LEIA, ANALISA, VERIFICA E REPORTA**
- Podes executar comandos de leitura/verificação (SELECT, cat, ls, pytest --collect-only, etc.)
- Gera um relatório detalhado com todas as descobertas

---

## 📌 CONTEXTO DO PROJETO

O **RealEstate Intelligence Engine** é um sistema autónomo empresarial para monitorização, avaliação e scoring de imóveis no mercado imobiliário português, com foco inicial no Porto mas com visão de expansão nacional.

### Localização do Projeto
- **Caminho:** `c:\Users\rodri\Desktop\Projeto analize mercado imobeleario`
- **Estrutura principal:** `realestate_engine/` (código principal) + diretórios de nível superior (scripts, configs, data, etc.)

### Stack Técnica
- **Core:** Python 3.8+ (objetivo: 3.14+)
- **Base de Dados:** SQLite atual (transitável para PostgreSQL)
- **Scraping:** nodriver, curl-cffi (anti-bot evasion)
- **ML/Valuation:** scikit-learn, xgboost, catboost, statsmodels
- **Dashboard:** Streamlit
- **Scheduler:** APScheduler
- **Monitoring:** Loguru, Prometheus
- **Cache:** Redis (opcional, atualmente não disponível)

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────┐
│                  Dashboard Streamlit                     │
│              (13 views: Overview, Search, Map, etc.)     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Notification Layer (Telegram)                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               Scoring Engine (5D Validation)              │
│  Discount 45% + Location 20% + Condition 15% +          │
│  Liquidity 10% + Freshness 10%                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Valuation Engine (Ensemble)                 │
│  Hedonic + XGBoost + Comparables + INE                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    ETL Layer                              │
│  Normalization → Deduplication → Geocoding → Enrichment  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               Scraping Layer (8 Portais)                  │
│  Idealista, Imovirtual, Casa Sapo, ERA, REMAX,          │
│  OLX, Century21, SuperCasa                               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Scheduler (APScheduler)                     │
│           Orquestração automática de jobs                │
└──────────────────────────────────────────────────────────┘
```

---

## 🔍 ESTADO ATUAL CONHECIDO (Baseado em Auditorias Anteriores)

### Base de Dados (SQLite)
- **Localização:** `data/db/micro_location_cache.db` e outras BDs
- **Estado atual:** Contém principalmente dados de teste/sample
- **Registros conhecidos:**
  - `raw_listings`: ~40 registros (todos sample data)
  - `clean_listings`: ~20 registros (todos sample data)
  - `valuations`: ~20 registros
  - `scores`: ~20 registros
  - `price_history`: ~13 registros
  - `notifications`: 0 registros
  - `watchlist`: 0 registros
  - `job_execution_log`: 0 registros (PROBLEMA: não está a ser preenchido)
  - `ine_data`: 0 registros

### Problemas Identificados em Auditorias Anteriores

#### 🔴 CRÍTICOS (Já Corrigidos)
1. **SQLite Foreign Keys Disabled** - Corrigido com `PRAGMA foreign_keys=ON`
2. **Orphan Data in Database** - Corrigido (limpeza de valuations/scores órfãos)
3. **Dashboard spider direct call** - Corrigido (removida chamada direta que crashava Streamlit)

#### 🟡 ALERTAS (Pendentes)
1. **ETL Data Loss (50%)** - 40 raw → 20 clean (causa desconhecida, precisa investigação)
2. **No Real Scraped Data** - Todos os dados são sample/sintéticos
3. **Redis Not Available** - Erro "connection refused" (afeta caching e queue)
4. **job_execution_log Empty** - Scheduler não está a registar execuções
5. **Notifications Empty** - Sistema de notificações nunca foi executado
6. **PostgreSQL Not Migrated** - Ainda em SQLite (objetivo: PostgreSQL para produção)

#### 🟠 SCRAPING (Problemas Conhecidos)
1. **Proxy Residencial Necessário** - Portais bloqueiam scraping sem proxy
2. **Seletores CSS Desatualizados** - Podem não funcionar com HTML atual
3. **Anti-bot Measures** - DataDome, Cloudflare requerem evasion avançado
4. **JavaScript Serialization** - Problemas com nodriver serializando objetos JS

### Testes (Estado Conhecido)
- **Total:** ~312+ testes
- **Unit Tests:** ~230 (todos passing)
- **Integration Tests:** ~30 (todos passing)
- **E2E Tests:** 12 (todos passing)
- **Stress/Chaos Tests:** 5 (todos passing)
- **Infrastructure Tests:** 8 (todos passing)
- **Data Quality Tests:** 8 (todos passing)
- **Pipeline Validators:** 19 (todos passing)
- **Critical Calculations:** 13 (todos passing)

---

## 📋 TAREFAS DE AUDITORIA E VERIFICAÇÃO

### 1. VERIFICAÇÃO DE ESTRUTURA DO PROJETO

**Objetivo:** Confirmar que todos os módulos e ficheiros necessários existem e estão organizados corretamente.

**Ações:**
1. Listar estrutura completa de diretórios em `realestate_engine/`
2. Verificar existência dos módulos principais:
   - `scraping/` (spiders para 8 portais)
   - `etl/` (normalizer, deduplicator, geocoder, enricher)
   - `valuation/` (hedonic_model, xgboost_model, comps_engine, ine_client, ensemble)
   - `scoring/` (scoring_engine, calculators individuais, red_flags_detector)
   - `database/` (models.py, repository.py)
   - `dashboard/` (app.py, views/)
   - `notification/` (telegram_bot, message_formatter)
   - `scheduler/` (orchestrator)
   - `monitoring/` (health checks, logging)
3. Verificar ficheiros de configuração:
   - `.env` (existência e variáveis definidas)
   - `requirements.txt` (dependências listadas)
   - `pyproject.toml` ou `setup.py` (se existir)
4. Verificar documentação:
   - `README.md` em `realestate_engine/`
   - Documentação em `docs/`
   - Planeamento em `planeamento/`

**Relatar:**
- Módulos em falta
- Ficheiros críticos ausentes
- Inconsistências na estrutura

---

### 2. VERIFICAÇÃO DE DEPENDÊNCIAS E AMBIENTE

**Objetivo:** Confirmar que todas as dependências estão instaladas e o ambiente está configurado.

**Ações:**
1. Ler `requirements.txt` e listar todas as dependências
2. Verificar versões do Python instaladas
3. Verificar se pacotes críticos estão instalados:
   - `nodriver` ou `curl-cffi`
   - `streamlit`
   - `sqlalchemy`
   - `pandas`
   - `scikit-learn`
   - `xgboost`
   - `catboost` (se especificado)
   - `apscheduler`
   - `loguru`
4. Verificar se Redis está disponível (tentar conexão)
5. Verificar se PostgreSQL está disponível (opcional)

**Relatar:**
- Dependências em falta
- Versões incompatíveis
- Serviços externos não disponíveis (Redis, PostgreSQL)

---

### 3. VERIFICAÇÃO DA BASE DE DADOS

**Objetivo:** Analisar o estado atual da base de dados e identificar problemas.

**Ações:**
1. Localizar todos os ficheiros de base de dados (.db, .sqlite, .sqlite3)
2. Para cada BD:
   - Listar todas as tabelas
   - Contar registros em cada tabela
   - Verificar schema de cada tabela
   - Identificar tabelas vazias que não deveriam estar
   - Verificar integridade referencial (foreign keys)
   - Identificar dados órfãos
3. Analisar qualidade dos dados:
   - Percentagem de valores nulos em campos críticos (preco, area, quartos)
   - Valores fora de intervalos razoáveis (preços negativos, áreas < 10m², etc.)
   - Duplicados óbvios
4. Verificar se `job_execution_log` está a ser preenchido
5. Verificar se há dados reais (não sample) nas tabelas

**Relatar:**
- Estado detalhado de cada tabela
- Problemas de integridade
- Qualidade dos dados
- Dados órfãos
- Tabelas que deveriam ter dados mas estão vazias

---

### 4. VERIFICAÇÃO DO SCRAPING LAYER

**Objetivo:** Avaliar a capacidade de scraping e identificar problemas.

**Ações:**
1. Listar todos os spiders em `realestate_engine/scraping/spiders/`
2. Para cada spider:
   - Ler o código fonte
   - Verificar se usa nodriver ou curl-cffi
   - Verificar se tem proxy rotation configurado
   - Verificar se tem anti-bot evasion
   - Identificar seletores CSS usados
   - Verificar se há funções de fallback para extração de dados
3. Verificar se há ficheiros de configuração de proxy
4. Verificar se há testes específicos para cada spider
5. Analisar logs de scraping em `logs/scraping/` se existirem

**Relatar:**
- Spiders existentes vs. esperados (8 portais)
- Problemas de configuração
- Falta de proxy/stealth
- Seletores CSS potencialmente desatualizados
- Ausência de testes

---

### 5. VERIFICAÇÃO DO ETL LAYER

**Objetivo:** Verificar se o pipeline ETL está correto e identificar a causa da perda de 50% de dados.

**Ações:**
1. Ler código de cada componente ETL:
   - `normalizer.py` - normalização de preço, área, quartos, localização
   - `deduplicator.py` - algoritmo de fingerprint e deduplicação
   - `geocoder.py` - geocodificação e cache
   - `enricher.py` - enriquecimento com INE, POIs, etc.
2. Analisar o deduplicator:
   - Verificar algoritmo de fingerprint
   - Verificar bucket sizes (price, area, location)
   - Identificar se está demasiado agressivo
3. Analisar o validator:
   - Verificar thresholds de rejeição
   - Verificar campos obrigatórios
   - Verificar regras de saneamento
4. Verificar se há testes de E2E para o pipeline completo
5. Executar (apenas leitura) uma análise dos dados para entender a perda:
   - Comparar raw vs clean listings
   - Identificar quais critérios rejeitam dados

**Relatar:**
- Componentes em falta
- Problemas no algoritmo de deduplicação
- Thresholds demasiado restritivos
- Causa provável da perda de 50%
- Falta de testes E2E

---

### 6. VERIFICAÇÃO DO VALUATION ENGINE

**Objetivo:** Confirmar que o motor de avaliação está completo e funcional.

**Ações:**
1. Verificar existência de todos os modelos:
   - `hedonic_model.py`
   - `xgboost_model.py`
   - `comps_engine.py`
   - `ine_client.py`
   - `weighted_ensemble.py`
   - `confidence_interval.py` (se existir)
2. Ler código de cada modelo:
   - Verificar se está implementado (não apenas stub)
   - Verificar se tem treinamento/inference
   - Verificar se usa features adequadas
   - Verificar se tem fallback mechanisms
3. Verificar se há modelos treinados salvos
4. Verificar se há testes unitários para cada modelo
5. Analisar se o ensemble está corretamente implementado
6. Verificar se há SHAP explanations (se especificado nos requisitos)

**Relatar:**
- Modelos em falta
- Implementações incompletas
- Falta de modelos treinados
- Falta de testes
- Problemas no ensemble

---

### 7. VERIFICAÇÃO DO SCORING ENGINE

**Objetivo:** Confirmar que o motor de scoring está completo e funcional.

**Ações:**
1. Verificar existência de todos os componentes:
   - `scoring_engine.py`
   - `score_location_calculator.py`
   - `score_discount_calculator.py`
   - `score_condition_calculator.py`
   - `score_liquidity_calculator.py`
   - `score_freshness_calculator.py`
   - `red_flags_detector.py`
   - `weighted_score_calculator.py`
   - `rationale_generator.py` (se existir)
2. Ler código de cada calculator:
   - Verificar se está implementado
   - Verificar se retorna scores entre 0-10
   - Verificar se tem fallback para dados em falta
3. Verificar se há testes unitários para cada calculator
4. Analisar se o weighted score está corretamente implementado (45% + 20% + 15% + 10% + 10%)
5. Verificar se red flags detector está funcional

**Relatar:**
- Calculators em falta
- Implementações incompletas
- Falta de testes
- Problemas na ponderação

---

### 8. VERIFICAÇÃO DO DASHBOARD

**Objetivo:** Confirmar que o dashboard está completo e funcional.

**Ações:**
1. Verificar estrutura de `realestate_engine/dashboard/`
2. Listar todas as views (esperado: 13 views)
3. Para cada view:
   - Ler o código fonte
   - Verificar se carrega dados corretamente
   - Verificar se há tratamento de erros
   - Verificar se há filtros implementados
4. Verificar `app.py` principal:
   - Configuração de navegação
   - Autenticação (se aplicável)
   - Tratamento de erros globais
5. Verificar se há testes de UI (Playwright ou similar)
6. Verificar se o dashboard pode ser iniciado sem erros

**Relatar:**
- Views em falta
- Problemas de carregamento de dados
- Falta de tratamento de erros
- Falta de testes de UI
- Problemas de navegação

---

### 9. VERIFICAÇÃO DO SCHEDULER

**Objetivo:** Confirmar que o scheduler está configurado e a funcionar.

**Ações:**
1. Ler código do orchestrator em `realestate_engine/scheduler/`
2. Verificar jobs configurados:
   - Scraping job
   - ETL job
   - Valuation job
   - Scoring job
   - Notification job
3. Verificar intervalos de execução
4. Verificar dependências entre jobs
5. Verificar se há logging de execução (porque `job_execution_log` está vazio)
6. Verificar se há tratamento de erros e retry logic
7. Verificar scripts de inicialização:
   - `start_scheduler.bat`
   - `start_system.bat`
   - `run_scrapers.bat`

**Relatar:**
- Jobs em falta
- Problemas de configuração
- Causa de `job_execution_log` vazio
- Falta de retry logic
- Scripts de inicialização com problemas

---

### 10. VERIFICAÇÃO DO NOTIFICATION ENGINE

**Objetivo:** Confirmar que o sistema de notificações está configurado.

**Ações:**
1. Verificar existência de componentes:
   - `notification_engine.py`
   - `telegram_bot.py`
   - `message_formatter.py`
   - `opportunity_selector.py`
2. Ler código de cada componente
3. Verificar configuração do Telegram no `.env`:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Verificar se há testes de notificações
5. Verificar se notificações já foram enviadas (tabela `notifications`)

**Relatar:**
- Componentes em falta
- Configuração incompleta
- Falta de credenciais
- Falta de testes
- Razão pela qual nunca foram enviadas

---

### 11. VERIFICAÇÃO DE MONITORING E LOGGING

**Objetivo:** Confirmar que o sistema tem monitoring e logging adequados.

**Ações:**
1. Verificar logs existentes em `logs/`:
   - `dashboard.log`
   - `engine.log`
   - `errors.log`
   - `scraping/` (se existir)
2. Analisar conteúdo dos logs recentes
3. Verificar se há health checks implementados
4. Verificar se há integração com Prometheus
5. Verificar se há alertas configurados
6. Verificar se há data quality monitoring

**Relatar:**
- Logs em falta
- Problemas de logging
- Falta de health checks
- Falta de monitoring
- Problemas encontrados nos logs

---

### 12. VERIFICAÇÃO DE TESTES

**Objetivo:** Confirmar que a suite de testes está completa e executar testes (apenas verificação).

**Ações:**
1. Listar todos os testes em `tests/` e `realestate_engine/tests/`
2. Categorizar testes:
   - Unit tests
   - Integration tests
   - E2E tests
   - Performance tests
   - Chaos tests
3. Executar `pytest --collect-only` para listar todos os testes
4. Verificar coverage de testes (se `pytest-cov` disponível)
5. Identificar módulos sem testes
6. Identificar funcionalidades críticas sem testes

**Relatar:**
- Total de testes por categoria
- Módulos sem cobertura
- Funcionalidades críticas sem testes
- Coverage percentage (se disponível)

---

### 13. VERIFICAÇÃO DE DOCUMENTAÇÃO

**Objetivo:** Avaliar a qualidade e completude da documentação.

**Ações:**
1. Ler documentação principal:
   - `README.md` (raiz e `realestate_engine/`)
   - `docs/PROJECT_STRUCTURE.md`
   - `docs/README.md`
   - Planeamento em `planeamento/`
2. Verificar se há documentação para:
   - Instalação
   - Configuração
   - Execução
   - Troubleshooting
   - Arquitetura
   - API (se aplicável)
3. Verificar se há código comentado adequadamente
4. Verificar se há docstrings em funções/classes

**Relatar:**
- Documentação em falta
- Documentação desatualizada
- Falta de docstrings
- Falta de guias de uso

---

### 14. VERIFICAÇÃO DE INFRAESTRUTURA E DEPLOYMENT

**Objetivo:** Confirmar que o projeto está pronto para deployment.

**Ações:**
1. Verificar `docker-compose.yml`:
   - Serviços configurados
   - Variáveis de ambiente
   - Volumes e networks
2. Verificar `Dockerfile` (se existir)
3. Verificar CI/CD em `.github/workflows/`:
   - Workflows configurados
   - Testes automatizados
   - Build e deploy
4. Verificar scripts de deployment:
   - `install_windows.bat`
   - Outros scripts de setup
5. Verificar se há configuração de produção vs desenvolvimento

**Relatar:**
- Infraestrutura em falta
- Configuração incompleta
- Falta de CI/CD
- Problemas de deployment

---

### 15. VERIFICAÇÃO DE SEGURANÇA

**Objetivo:** Identificar problemas de segurança.

**Ações:**
1. Verificar se há credenciais hardcoded no código
2. Verificar se `.env` está no `.gitignore`
3. Verificar se há tokens sensíveis nos logs
4. Verificar se o dashboard tem autenticação
5. Verificar se a BD é acessível via web
6. Verificar se há rate limiting implementado
7. Verificar se há validação de input

**Relatar:**
- Credenciais expostas
- Falta de autenticação
- Falta de rate limiting
- Vulnerabilidades de segurança

---

### 16. VERIFICAÇÃO DE PERFORMANCE

**Objetivo:** Avaliar se o sistema tem performance adequada.

**Ações:**
1. Verificar se há testes de performance
2. Verificar se há benchmarks
3. Analisar se há caching implementado
4. Verificar se há otimizações de queries
5. Verificar se há lazy loading onde aplicável

**Relatar:**
- Falta de testes de performance
- Falta de caching
- Queries não otimizadas
- Gargalos de performance identificados

---

### 17. VERIFICAÇÃO DE REQUISITOS NÃO IMPLEMENTADOS

**Objetivo:** Comparar com os requisitos e identificar o que falta.

**Ações:**
1. Ler `.gsd/REQUIREMENTS.md`
2. Para cada requisito:
   - Verificar se está implementado
   - Verificar se está testado
   - Verificar se está documentado
3. Ler `.gsd/ROADMAP.md`
4. Verificar progresso em cada fase
5. Identificar requisitos críticos não implementados

**Relatar:**
- Requisitos não implementados
- Requisitos parcialmente implementados
- Requisitos implementados mas não testados
- Prioridade de implementação

---

### 18. VERIFICAÇÃO DE PRODUCTION READINESS

**Objetivo:** Determinar se o sistema está pronto para produção.

**Ações:**
1. Criar checklist de production readiness:
   - Scraping funcional com dados reais
   - ETL processando dados corretamente
   - Valuation engine treinado e funcional
   - Scoring engine funcional
   - Dashboard operacional
   - Notificações configuradas
   - Scheduler a executar
   - Monitoring ativo
   - Logs funcionais
   - Health checks
   - Backup strategy
   - Error handling
   - Security measures
   - Performance adequate
   - Test coverage adequate
   - Documentation complete
   - CI/CD configured
   - Deployment ready
2. Avaliar cada item
3. Identificar blockers para produção

**Relatar:**
- Status de production readiness
- Blockers críticos
- Recomendações para atingir production-ready
- Timeline estimada

---

## 📊 FORMATO DO RELATÓRIO FINAL

A IA deve gerar um relatório detalhado com as seguintes secções:

### 1. RESUMO EXECUTIVO
- Visão geral do estado do projeto
- Status de production readiness (Ready / Not Ready / Partially Ready)
- Número de problemas críticos/altos/médios/baixos
- Timeline estimada para production-ready

### 2. ESTRUTURA DO PROJETO
- Módulos existentes vs. esperados
- Ficheiros críticos em falta
- Inconsistências estruturais

### 3. DEPENDÊNCIAS E AMBIENTE
- Dependências instaladas vs. requeridas
- Versões incompatíveis
- Serviços externos disponíveis

### 4. BASE DE DADOS
- Estado detalhado de cada tabela
- Problemas de integridade
- Qualidade dos dados
- Dados órfãos

### 5. SCRAPING LAYER
- Spiders existentes vs. esperados
- Problemas de configuração
- Falta de proxy/stealth
- Capacidade de scraping atual

### 6. ETL LAYER
- Componentes em falta
- Problemas de deduplicação
- Causa da perda de 50%
- Recomendações

### 7. VALUATION ENGINE
- Modelos implementados vs. esperados
- Estado dos modelos treinados
- Problemas identificados
- Recomendações

### 8. SCORING ENGINE
- Componentes implementados vs. esperados
- Problemas identificados
- Recomendações

### 9. DASHBOARD
- Views implementadas vs. esperadas
- Problemas de carregamento
- Falta de testes de UI
- Recomendações

### 10. SCHEDULER
- Jobs configurados vs. esperados
- Causa de `job_execution_log` vazio
- Problemas identificados
- Recomendações

### 11. NOTIFICATION ENGINE
- Componentes implementados vs. esperados
- Configuração incompleta
- Razão de não funcionar
- Recomendações

### 12. MONITORING E LOGGING
- Logs existentes
- Problemas encontrados
- Falta de monitoring
- Recomendações

### 13. TESTES
- Total de testes por categoria
- Coverage por módulo
- Módulos sem cobertura
- Funcionalidades críticas sem testes

### 14. DOCUMENTAÇÃO
- Documentação existente
- Documentação em falta
- Documentação desatualizada
- Recomendações

### 15. INFRAESTRUTURA E DEPLOYMENT
- Serviços configurados
- CI/CD status
- Problemas de deployment
- Recomendações

### 16. SEGURANÇA
- Vulnerabilidades encontradas
- Credenciais expostas
- Falta de segurança
- Recomendações

### 17. PERFORMANCE
- Testes de performance existentes
- Gargalos identificados
- Recomendações

### 18. REQUISITOS NÃO IMPLEMENTADOS
- Lista de requisitos não implementados
- Prioridade de cada um
- Esforço estimado

### 19. PRODUCTION READINESS CHECKLIST
- Checklist completo com status de cada item
- Blockers críticos
- Itens pendentes

### 20. RECOMENDAÇÕES PRIORITÁRIAS
- Top 10 ações prioritárias (ordenadas por impacto)
- Timeline estimada
- Dependências entre ações

### 21. CONCLUSÃO
- Veredito final sobre production readiness
- Próximos passos recomendados

---

## 🎨 ESTILO E TOM DO RELATÓRIO

- **Profissional e técnico** - Usar terminologia adequada
- **Objetivo e baseado em factos** - Apoiar todas as afirmações com evidências
- **Conciso mas detalhado** - Ir direto ao ponto mas fornecer detalhes quando necessário
- **Ação-orientado** - Focar em recomendações acionáveis
- **Estruturado** - Usar listas, tabelas e formatação clara
- **Português** - Todo o relatório em português (com termos técnicos em inglês quando apropriado)

---

## 🚫 RESTRIÇÕES IMPORTANTES

**A IA NÃO DEVE:**
- Fazer alterações em qualquer ficheiro
- Executar comandos de escrita na base de dados
- Instalar pacotes
- Modificar configurações
- Criar novos ficheiros
- Deletar ficheiros
- Executar scripts que modifiquem o estado

**A IA PODE:**
- Ler ficheiros
- Listar diretórios
- Executar comandos de leitura (SELECT, cat, ls, etc.)
- Executar `pytest --collect-only` (não executar testes que modifiquem BD)
- Analisar código
- Verificar logs
- Gerar relatórios

---

## ✅ CRITÉRIOS DE SUCESSO

A auditoria será considerada bem-sucedida se:

1. **Todos os módulos foram verificados** - Nenhum componente crítico foi omitido
2. **Todos os problemas foram identificados** - Críticos, altos, médios e baixos
3. **Causas raiz foram determinadas** - Não apenas sintomas
4. **Recomendações são acionáveis** - Específicas e priorizadas
5. **Relatório é completo** - Todas as secções foram preenchidas
6. **Nenhuma alteração foi feita** - Estado do sistema permanece inalterado
7. **Production readiness foi avaliada** - Com veredito claro e blockers identificados

---

## 📞 INFORMAÇÃO ADICIONAL

Se durante a auditoria a IA encontrar informações insuficientes para completar uma verificação, deve:
1. Documentar o que foi verificado
2. Explicar o que não pôde ser verificado
3. Explicar por que não foi possível
4. Sugerir como obter essa informação

A IA deve ser transparente sobre limitações e incertezas.

---

## 🎯 OBJETIVO FINAL

O objetivo desta auditoria é fornecer um **diagnóstico completo e profissional** do estado atual do RealEstate Engine, identificando todos os problemas, gaps e blockers que impedem o sistema de estar production-ready, e fornecer recomendações claras e priorizadas para atingir esse estado.

O relatório deve ser **suficientemente detalhado** para que uma equipa de desenvolvimento possa agir sobre as recomendações sem necessidade de investigação adicional.

---

**INÍCIO DA AUDITORIA**
