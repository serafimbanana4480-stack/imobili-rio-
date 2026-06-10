# 22 — Plataforma Inteligente Auto-Auditável e Production-Grade

## Objetivo

Evoluir o Real Estate Opportunity Engine de um sistema production-ready para uma plataforma:

- Auto-auditável.
- Data-driven.
- Explicável com Explainable AI.
- Observável em tempo real.
- Capaz de validar as suas próprias decisões técnicas.
- Preparada para venda com métricas, ROI e explicabilidade demonstráveis.

O sistema deixa de ser apenas uma aplicação de scraping, API e dashboard. Passa a ser uma plataforma inteligente de análise imobiliária com melhoria contínua baseada em dados reais, benchmarks, telemetria, auditoria técnica e análise externa online.

## Decisão Arquitetural

Não fazer um rewrite total imediato. A arquitetura existente já está modularizada em `scraping`, `etl`, `database`, `api`, `valuation`, `scoring`, `scheduler`, `monitoring`, `security` e `dashboard`, conforme `planeamento/03-arquitetura-sistema.md` e `planeamento/17-estrutura-projecto.md`.

A estratégia correta é hardening incremental com compatibilidade e introdução de uma nova camada transversal:

## Nova Camada Transversal — Meta Layer (Self-Improving System)

A `Meta Layer` é responsável por:

- Auditoria contínua do sistema.
- Benchmarking de performance.
- Validação da stack tecnológica.
- Avaliação de custo vs performance.
- Análise de modelos ML: drift, bias, explicabilidade e degradação.
- Sugestões automáticas de otimização técnica.
- Geração de relatórios executivos para venda, operação e tomada de decisão.

Princípios:

1. Manter FastAPI, SQLAlchemy 2.x, PostgreSQL/SQLite, Redis, nodriver, XGBoost/SHAP e Prometheus.
2. Corrigir riscos de produção existentes.
3. Introduzir abstrações de queue/cache/security sem quebrar o modo local.
4. Preparar o sistema para escalar para Celery/Redis/PostgreSQL/containers.
5. Adicionar inteligência operacional sem acoplar a Meta Layer aos módulos de negócio.
6. Validar cada decisão com métricas reais antes de avançar para otimização automática.

## Escopo

### Fase A — Baseline e Segurança API

- Rever configuração centralizada.
- Remover defaults inseguros de JWT.
- Tornar CORS restritivo por configuração.
- Adicionar headers de segurança HTTP.
- Proteger endpoints mutáveis com autenticação configurável.
- Garantir rate limiting com fallback local e Redis quando disponível.

### Fase B — Scraping Robusto

- Consolidar user-agent rotation.
- Garantir proxy rotation configurável por portal.
- Normalizar retry/backoff e bloqueio por portal.
- Adicionar fallback strategy explícita para spiders directos vs browser.
- Evitar bypass antiético de robots/termos; respeitar throttling configurável.

### Fase C — Performance e Cache

- Adicionar cache comum com interface `CacheBackend`.
- Usar Redis quando disponível e fallback em memória/SQLite quando local.
- Cachear geocoding, POI, valuation e AI thesis.
- Reduzir recomputação em dashboard/API.

### Fase D — Database Production Readiness

- Validar índices existentes.
- Adicionar índices compostos para queries frequentes.
- Garantir SQLite WAL no modo local.
- Garantir pooling seguro para PostgreSQL.
- Evitar `create_all` como substituto de migrations em produção.

### Fase E — API Production Readiness

- Garantir paginação, filtros e ordenação nos endpoints de listings.
- Padronizar respostas de erro.
- Adicionar endpoint de readiness/liveness separado.
- Garantir schemas Pydantic consistentes.

### Fase F — Queue/Workers

- Introduzir camada de task queue compatível com execução local.
- Implementar adapter local inicialmente.
- Preparar Celery + Redis como opcional production profile.
- Não substituir APScheduler antes de testes de regressão.

### Fase G — DevOps e Observabilidade

- Corrigir Dockerfile para Python 3.12 e instalação via `pyproject.toml`.
- Corrigir `docker-compose.yml` para secrets/config sem passwords hardcoded.
- Adicionar healthchecks coerentes.
- Preparar Prometheus config e logs estruturados.

### Fase H — Validação Final

- Executar testes curados.
- Adicionar testes de regressão para alterações de segurança, cache e API.
- Corrigir falhas encontradas.
- Atualizar documentação final com arquitetura, stack e decisões.

### Fase I — Auditoria Online Inteligente

Objetivo:

- Permitir que o sistema compare as suas decisões técnicas com o estado atual da indústria 2025–2026.
- Transformar auditorias manuais em relatórios automáticos e recorrentes.

Implementação:

- Criar módulo `realestate_engine/meta/tech_audit_engine.py`.
- Criar contratos para fontes externas: documentação oficial, benchmarks públicos, GitHub trends e APIs públicas quando possível.
- Avaliar frameworks, bibliotecas críticas, estratégias de scraping, arquitetura, observabilidade, segurança e custos.
- Guardar resultados em tabela própria ou ficheiros versionados em `data/meta/audits/`.
- Produzir relatório automático:
  - Stack atual vs melhores práticas.
  - Alternativas modernas.
  - Risco de obsolescência.
  - Recomendações com prioridade, custo e risco.

Critérios de aceitação:

- Relatório gerado sem alterar código automaticamente.
- Cada recomendação inclui evidência, data, fonte e confiança.
- O sistema distingue recomendação informativa de recomendação acionável.

### Fase J — Inteligência de Modelos (XGBoost + SHAP)

Objetivo:

- Transformar scoring e valuation em componentes explicáveis, auditáveis e confiáveis para venda.

Stack:

- XGBoost para preço estimado e probabilidade de oportunidade.
- SHAP para explicações por feature e impacto individual por imóvel.

Implementação:

- Formalizar datasets de treino para valuation e scoring.
- Treinar modelos XGBoost para:
  - Preço estimado.
  - Probabilidade de oportunidade.
- Integrar SHAP para:
  - Explicação por feature.
  - Visualização de impacto.
  - Justificações por imóvel.
- Guardar artefactos de modelo, métricas e versão de features.
- Expor explicações na API e dashboard.

Resultado por imóvel:

- Score.
- Valor estimado.
- Confiança.
- Justificação explicável:
  - “Preço abaixo da média devido a localização X”.
  - “Alta oportunidade devido a desconto Y e liquidez Z”.

Critérios de aceitação:

- Cada score crítico tem explicação SHAP ou fallback racional.
- Métricas de treino e validação ficam persistidas.
- Modelos são versionados.

### Fase K — Model Monitoring & Drift Detection

Problema:

- Modelos degradam com o tempo devido a mudanças no mercado, portais, dados e comportamento de preços.

Objetivo:

- Detetar degradação antes de afetar decisões.

Implementação:

- Monitorizar:
  - Data drift.
  - Feature drift.
  - Prediction drift.
  - Mudanças na distribuição de preço, área, localização, desconto e score.
- Comparar distribuição atual vs baseline de treino.
- Criar alertas quando drift excede thresholds.
- Preparar re-treino automático opcional, mas manter aprovação manual antes de promover modelo para produção.

Critérios de aceitação:

- Drift report periódico.
- Alertas quando features críticas mudam.
- Modelo em produção mostra versão, data, métricas e baseline.

### Fase L — Observabilidade Total

Objetivo:

- Ter visibilidade operacional em tempo real sobre scraping, API, DB, ML e Meta Layer.

Stack:

- Prometheus.
- Logging estruturado JSON.
- Métricas customizadas.
- Grafana/Loki como opção recomendada para produção.

Métricas críticas:

- Taxa de bloqueio por portal.
- Latência por endpoint.
- Tempo de scraping.
- Throughput de dados.
- Uso CPU/RAM.
- Cache hit ratio.
- Tempo de resposta DB.
- Tempo de inferência ML.
- Tempo de geração SHAP.
- Número de recomendações da Meta Layer por severidade.

Critérios de aceitação:

- Endpoint de métricas cobre scraping, API, DB, cache, ML e filas.
- Logs estruturados não expõem dados pessoais nem secrets.
- Dashboard operacional documentado.

### Fase M — Alerting Inteligente

Objetivo:

- Transformar métricas em alertas acionáveis.

Alertas baseados em:

- Thresholds.
- Anomalias.
- Degradação histórica.

Exemplos:

- “Scraper X bloqueado 80%”.
- “DB latency aumentou 3x”.
- “Modelo perdeu precisão”.
- “Cache hit ratio caiu abaixo de 40%”.
- “Custo por lead subiu acima do limite”.

Critérios de aceitação:

- Alertas têm severidade, causa provável e ação recomendada.
- Alertas críticos podem ser enviados por Telegram.
- Falsos positivos são registados para ajuste futuro.

### Fase N — Benchmarking Contínuo

Objetivo:

- Garantir que o sistema continua competitivo ao longo do tempo.

Implementação:

- Testar periodicamente:
  - Velocidade de scraping.
  - Eficiência de queries.
  - Latência da API.
  - Tempo de ETL.
  - Tempo de valuation/scoring.
  - Custos de infraestrutura.
- Comparar com:
  - Baselines históricos internos.
  - Alternativas técnicas avaliadas pela Fase I.

Critérios de aceitação:

- Benchmarks têm baseline, data, versão do código e ambiente.
- Regressões de performance geram alertas.
- Resultados alimentam a Fase O.

### Fase O — Otimização Automática Assistida

Objetivo:

- Fazer o sistema sugerir melhorias técnicas de forma autónoma, mas sem aplicar mudanças destrutivas sem aprovação.

Exemplos:

- “Trocar biblioteca X por Y”.
- “Adicionar índice na tabela Z”.
- “Aumentar workers”.
- “Reduzir concorrência do portal X por bloqueios”.
- “Ativar cache para query Y”.

Implementação:

- Criar motor de recomendações técnicas baseado em métricas, benchmarks, auditoria online e logs.
- Classificar recomendações por impacto, risco, esforço e confiança.
- Gerar propostas de alteração como planos, não como alterações automáticas diretas.

Critérios de aceitação:

- Nenhuma alteração destrutiva é aplicada sem aprovação.
- Recomendações têm evidência objetiva.
- Recomendações repetidas são consolidadas.

### Fase P — Segurança Avançada

Objetivo:

- Manter segurança continuamente auditada.

Auditoria contínua:

- Dependências vulneráveis.
- Configurações inseguras.
- Secrets ausentes, fracos ou expostos.
- CORS, headers, rate limiting e autenticação.
- Rotação de secrets.
- Hardening automático quando seguro.

Critérios de aceitação:

- Relatório de segurança recorrente.
- Falhas críticas bloqueiam modo produção.
- Secrets nunca aparecem em logs ou relatórios.

### Fase Q — Data Quality Layer

Problema:

- Dados de scraping são inconsistentes, incompletos e podem degradar modelos.

Objetivo:

- Garantir qualidade mensurável por entrada, portal e pipeline.

Implementação:

- Validadores para:
  - Outliers.
  - Dados incompletos.
  - Tipos inválidos.
  - Campos impossíveis.
  - Duplicados.
  - Inconsistências entre preço, área, localização e tipologia.
- Score de qualidade por listing.
- Métricas de qualidade por portal.

Critérios de aceitação:

- Cada listing tem score de qualidade ou razão para não ter.
- Dados com baixa qualidade são excluídos ou degradados no scoring.
- Métricas de qualidade alimentam alertas e drift detection.

### Fase R — Feature Store (Opcional Avançado)

Objetivo:

- Centralizar features usadas em ML para reutilização, consistência e versionamento.

Implementação:

- Criar camada `features/store.py` com backend inicial SQL/SQLite/PostgreSQL.
- Versionar feature sets.
- Reutilizar features em scoring, valuation, model monitoring e SHAP.

Critérios de aceitação:

- Features críticas têm nome, versão, origem e data de cálculo.
- Treino e inferência usam o mesmo contrato de features.

### Fase S — Custos e Eficiência

Objetivo:

- Tornar o sistema vendável e sustentável economicamente.

Monitorizar:

- Custo por scraping.
- Custo por lead.
- Custo por insight.
- Custo por análise LLM.
- Custo por portal.
- Custo de infraestrutura por dia/mês.

Critérios de aceitação:

- Relatório de custo por ciclo.
- Alertas quando custo por lead excede threshold.
- ROI estimado disponível para venda.

### Fase T — Preparação para Venda

Objetivo:

- Transformar o sistema em produto vendável com confiança técnica e comercial.

Requisitos:

- Explicabilidade com SHAP.
- Métricas claras.
- Estabilidade comprovada.
- Documentação técnica.
- ROI demonstrável.
- Relatórios automáticos.
- Runbooks de operação.
- Perfil de deployment documentado: local, VPS e cloud.

Critérios de aceitação:

- Demo end-to-end com dados reais ou amostra realista.
- Relatório executivo exportável.
- Documentação para instalação, operação e troubleshooting.
- Checklist de venda concluída.

## Arquitetura Final Evoluída

Camadas:

1. Scraping Layer.
2. Processing Layer.
3. Storage Layer.
4. API Layer.
5. ML Layer (XGBoost + SHAP).
6. Observability Layer (Prometheus, logs estruturados, alertas).
7. Meta Layer (auditoria, benchmarking, otimização e validação técnica).

Fluxo de alto nível:

```text
Portais/API externas
    ↓
Scraping Layer
    ↓
Processing + Data Quality Layer
    ↓
Storage + Feature Store
    ↓
Valuation + Scoring + Explainability
    ↓
API + Dashboard + Notifications
    ↓
Observability Layer
    ↓
Meta Layer
    ↺ recomenda melhorias, detecta drift, audita stack e valida custos
```

## Restrições

- Não reescrever o sistema em microservices nesta fase; isso é Fase 3 do roadmap de escala global e aumentaria risco operacional.
- Não remover Streamlit nesta fase; preparar API e segurança primeiro. Frontend Next.js fica como fase posterior se o produto for SaaS público.
- Não hardcodar secrets.
- Não reduzir scraping ethics; throttling e robots/termos continuam requisitos.
- Não permitir que a Meta Layer aplique mudanças destrutivas sem aprovação explícita.
- Não tratar auditoria online como verdade absoluta: recomendações externas devem ter confiança, fonte e data.

## Critérios de Aceitação

- API sem CORS aberto por defeito em produção.
- JWT não aceita secret default em produção.
- Headers de segurança ativos.
- Docker e compose sem passwords hardcoded obrigatórias.
- Cache comum com fallback local.
- Scraping com retry/backoff/proxy/user-agent centralizáveis.
- SQLite local com WAL; PostgreSQL com pooling configurável.
- Testes relevantes a passar.
- README/produção atualizado com estrutura e stack final.
- Sistema explica decisões de ML.
- Métricas disponíveis em tempo real.
- Alertas funcionais.
- Auditoria automática ativa.
- Stack validada continuamente.
- Performance monitorizada.
- Dados com qualidade garantida.
- Custos por lead/insight estimáveis.

## Ordem de Implementação

1. Segurança API e configuração.
2. Cache/performance base.
3. Database hardening.
4. Scraping hardening.
5. Docker/DevOps.
6. Data Quality Layer.
7. Observabilidade total.
8. Explainable ML com XGBoost + SHAP.
9. Model monitoring e drift detection.
10. Alerting inteligente.
11. Benchmarking contínuo.
12. Meta Layer de auditoria online.
13. Otimização automática assistida.
14. Custos/eficiência e preparação para venda.
15. Testes, documentação e validação final.

## Veredicto Arquitetural

O sistema deixa de ser:

> “um scraper com API”

E passa a ser:

> “uma plataforma inteligente de análise imobiliária com auto-otimização, explicabilidade e validação técnica contínua”.

## Estado

Planeado para implementação incremental.

Cada fase deve ser validada com métricas reais antes de avançar. A Meta Layer deve começar como modo “read-only advisory” e só evoluir para automação assistida após existirem métricas, testes e critérios de confiança suficientes.
