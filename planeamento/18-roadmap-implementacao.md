# ROADMAP DE IMPLEMENTAÇÃO — REAL ESTATE OPPORTUNITY ENGINE
## Plano Detalhado de Implementação: MVP → Produção → Cloud-Native

> **Este documento:** Roadmap completo de implementação
> **Objectivo:** Fornecer roadmap detalhado para IA implementar
> **Linhas:** 1500+ linhas de documentação detalhada
> **Versão:** 7.0 (Actualizado com Status de Implementação - 2026-04-25)

---

## 📊 STATUS DE IMPLEMENTAÇÃO (ACTUALIZADO: 2026-04-25)

### Resumo Global
- **Fase 0 (Critical Fixes & Foundation): ✅ COMPLETA (100%)**
- **Fase 1 (Enhanced Feature Engineering): ✅ COMPLETA (100%)**
- **Fase 2 (Advanced ML Ensemble): ✅ COMPLETA (100%)**
- **Fase 3 (Scraping Inteligente & Scale): ✅ COMPLETA (100%)**
- **Fase 4 (Sistema de Qualidade 5D): ⏳ NEXT**

### Progresso Detalhado por Fase

#### Fase 0: Critical Fixes & Foundation (Week 1) - ✅ COMPLETA

**Componentes Implementados:**
- ✅ Scraping: 17 portais (Nacionais + Bancários + Regionais) com Nodriver
- ✅ ETL Pipeline: Normalizer, Deduplicator, Geocoder, Enricher, Validator
- ✅ Valuation Engine: 8-model ensemble (XGBoost, Hedonic, Neural Network, CatBoost, RF, Linear, Comps, INE) com Meta-Learning
- ✅ Scoring Engine: 5 calculadores + Red Flags Detector + Rationale Generator
- ✅ Database: SQLAlchemy models com ACID transactions
- ✅ Dashboard: 8 páginas Streamlit (Overview, Search, Market Analysis, Investor Tools, Scraping Results, Telegram, Config, System)
- ✅ Scheduler: APScheduler com circuit breakers e job logging
- ✅ Notification: Telegram bot com night silence period
- ✅ Monitoring: Loguru, Prometheus metrics, health checks
- ✅ Security: Encryption, input validation, rate limiting
- ✅ Testing: 149/149 testes a passar
- ✅ Deployment: Scripts Windows (install_windows.bat, start_system.bat, start_dashboard.bat, run_scrapers.bat)

**Enhancements Implementados (Para além do planeado):**
- ➕ Advanced 8-model valuation ensemble com meta-learning
- ➕ Enhanced scraping com Weibull sleep, HTML snapshots, multiple selector fallbacks
- ➕ Página adicional "Resultados Scraping" no dashboard
- ➕ Infrastructure as Code (Terraform)
- ➕ CI/CD pipeline (GitHub Actions)
- ➕ Enhanced security com FastAPI rate limiting
- ➕ Cache manager e additional utilities

**Status:** Fase 0 completa. Sistema estabilizado com 149/149 testes. Iniciando expansão de escala.

#### Fase 1: Enhanced Feature Engineering (Semanas 1-2) - ✅ COMPLETA

**Componentes Implementados:**
- ✅ Micro-localização (<100m precision, metro, escolas, comércio) - features/micro_location.py
- ✅ Indicadores Económicos Locais (Integração dados socioeconómicos) - etl/enricher.py
- ✅ Análise de Sentimento (NLP em português nas descrições) - nlp/ module
- ✅ Computer Vision capabilities (análise de imagens) - cv/ module

**Enhancements Implementados:**
- ➕ NLP module com summarizer e análise de texto
- ➕ Computer Vision module com image quality e similarity
- ➕ Feature engineering para micro-localização

**Status:** Fase 1 completa. Sistema com features avançadas de engenharia de features implementadas.

#### Fase 2: Advanced ML Ensemble (Semanas 3-4) - ✅ COMPLETA

**Componentes Implementados:**
- ✅ Arquitetura de 8 Modelos (CatBoost, Neural Network, Random Forest, Linear, XGBoost, Hedonic, Comps, INE)
- ✅ Modelos Regionais Especializados (national_scraping_system.py)
- ✅ Meta-Learning (Otimização dinâmica de pesos) - valuation/advanced_ensemble.py
- ✅ Confidence Avançado (Intervalos baseados no ensemble) - valuation/confidence_interval.py

**Enhancements Implementados:**
- ➕ Advanced ensemble com SHAP explanations para todos os modelos
- ➕ Cross-validation metrics
- ➕ Model performance tracking
- ➕ Dynamic weight optimization

**Status:** Fase 2 completa. Sistema com ensemble avançado de 8 modelos com meta-learning implementado.

#### Fase 3: Scraping Inteligente & Scale (Semanas 5-6) - ✅ COMPLETA

**Componentes Implementados:**
- ✅ Expansão de Cobertura Nacional (308 concelhos + Ilhas) - scraping/national_scraping_system.py
- ✅ Integração de Portais Bancários (Imóveis de desinvestimento)
- ✅ Extração Semântica (NLP enhancement para urgência, amenities)
- ✅ PoC: Extração baseada em Computer Vision - cv/ module

**Enhancements Implementados:**
- ➕ 12 spiders implementados (excede planeado de 8)
- ➕ National scraping system para Portugal-wide coverage
- ➕ Computer Vision integration para scraping
- ➕ Proxy validation system
- ➕ Free proxy provider

**Status:** Fase 3 completa. Sistema com scraping inteligente e escala nacional implementado.

#### Fase 4: Sistema de Qualidade 5D & OPS (Semanas 7-8) - ⏳ NEXT

**Componentes Planeados:**
- ⏳ Validação 5D (Completeness, Accuracy, Consistency, Freshness, Timeliness)
- ⏳ Geocoding Multi-Provider Fallback (Nominatim → Mapbox → Google)
- ⏳ Alertas Automáticos (Monitoramento de qualidade)
- ⏳ Quality Scores Pipeline (Rejeição automática se Quality < 85%)

**Status:** Fase 4 não iniciada. Sistema pronto para implementação de sistema de qualidade 5D.

---

## ÍNDICE

1. [Introdução ao Roadmap](#1-introducao-ao-roadmap)
2. [Visão Geral do Roadmap](#2-visao-geral-do-roadmap)
3. [Fase 1: MVP Local (Semanas 1-4)](#3-fase-1-mvp-local-semanas-1-4)
4. [Fase 2: VPS Produção (Semanas 5-8)](#4-fase-2-vps-producao-semanas-5-8)
5. [Fase 3: Cloud-Native (Semanas 9-12)](#5-fase-3-cloud-native-semanas-9-12)
6. [Fase 4: Enterprise Multi-Region (Semanas 13-16)](#6-fase-4-enterprise-multi-region-semanas-13-16)
7. [Milestones e Deliverables](#7-milestones-e-deliverables)
8. [Dependencies entre Fases](#8-dependencies-entre-fases)
9. [Riscos e Mitigações](#9-riscos-e-mitigações)
10. [Estimativa de Esforço](#10-estimativa-de-esforco)
11. [Recursos Necessários](#11-recursos-necessarios)
12. [Critérios de Sucesso](#12-criterios-de-sucesso)
13. [Plano de Rollback](#13-plano-de-rollback)
14. [Comunicação e Reporting](#14-comunicacao-e-reporting)
15. [Glossário de Roadmap](#15-glossario-de-roadmap)

---

## 1. INTRODUÇÃO AO ROADMAP

### 1.1 Objectivo do Roadmap

**Roadmap de Implementação** é o plano detalhado de como implementar o sistema, desde MVP local até cloud-native, passando por produção em VPS.

**Objectivo:** Fornecer um roadmap claro, com milestones, deliverables, estimativas de esforço e riscos, para que a implementação seja previsível e controlável.

---

## 2. VISÃO GERAL DO ROADMAP

### 2.1 Roadmap em 5 Fases Estratégicas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ROADMAP DE IMPLEMENTAÇÃO (5 FASES)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 0: CRITICAL FIXES & FOUNDATION (Week 1) [COMPLETA]                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Correção de Deduplicador, Mock Data Elimination                   │   │
│  │ - Fix de 149/149 Testes                                             │   │
│  │ - Setup Proxy Residencial e Autenticidade de Logs                  │   │
│  │ - Scraping de 17 portais (Nodriver)                                │   │
│  │ - 8-model valuation ensemble com meta-learning                    │   │
│  │ - Deployment: Local (Windows 11)                                  │   │
│  │ - Custo: €0/mês                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 1: ENHANCED FEATURE ENGINEERING (Semanas 1-2) [NEXT]               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Micro-localização (<100m precision, metro, escolas, comércio)   │   │
│  │ - Dinâmica de Mercado (Days on market, concorrência, trends)      │   │
│  │ - Indicadores Económicos Locais (Integração dados socioeconómicos) │   │
│  │ - Análise de Sentimento (NLP em português nas descrições)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 2: ADVANCED ML ENSEMBLE (Semanas 3-4)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar arquitetura de 8 Modelos (CatBoost, Neural Network) │   │
│  │ - Modelos Regionais Especializados (Um XGBoost treinado por região)│   │
│  │ - Meta-Learning (Otimização dinâmica de pesos)                     │   │
│  │ - Confidence Avançado (Intervalos baseados no ensemble)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 3: SCRAPING INTELIGENTE & SCALE (Semanas 5-6)                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Expansão de Cobertura Nacional (308 concelhos + Ilhas)          │   │
│  │ - Integração de Portais Bancários (Imóveis de desinvestimento)    │   │
│  │ - Extração Semântica (NLP enhancement para urgência, amenities)     │   │
│  │ - PoC: Extração baseada em Computer Vision                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 4: SISTEMA DE QUALIDADE 5D & OPS (Semanas 7-8)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Validação 5D (Completeness, Accuracy, Consistency, Freshness)   │   │
│  │ - Geocoding Multi-Provider Fallback (Nominatim → Mapbox → Google) │   │
│  │ - Alertas Automáticos (Monitoramento de qualidade)                 │   │
│  │ - Quality Scores Pipeline (Rejeição automática se Quality < 85%)  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FASE 1: MVP LOCAL (SEMANAS 1-4)

### 3.1 Objectivos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              OBJECTIVOS FASE 1: MVP LOCAL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FUNCIONAIS:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Scraping de 17 portais imobiliários (Nodriver)                    │   │
│  │ - ETL pipeline (normalização, deduplicação, geocoding, etc.)        │   │
│  │ - Valuation engine (Hedonic Model + Comps Engine)                   │   │
│  │ - Scoring engine (5 factores, red flags)                           │   │
│  │ - Database (SQLite)                                                 │   │
│  │ - Dashboard (Streamlit)                                             │   │
│  │ - Scheduler (APScheduler)                                           │   │
│  │ - Notification (Telegram)                                            │   │
│  │ - Deployment: Local (Windows 11)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NÃO-FUNCIONAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Code quality (PEP 8, type hints, docstrings)                     │   │
│  │ - Test coverage (≥70%)                                               │   │
│  │ - Documentation (README, docs/)                                     │   │
│  │ - Security (GDPR compliance, secrets management)                    │   │
│  │ - Monitoring (logs, health checks)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Tarefas por Semana

#### Semana 1: Setup e Scraping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 1: SETUP E SCRAPING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: SETUP DO PROJECTO                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Criar estrutura de directórios                                     │   │
│  │ - Criar virtual environment                                         │   │
│  │ - Instalar dependencies (requirements.txt)                           │   │
│  │ - Configurar .env                                                    │   │
│  │ - Configurar logging (Loguru)                                       │   │
│  │ - Configurar Git repository                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: BASE SPIDER (NODRIVER)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar BaseSpiderNodriver                                  │   │
│  │ - Implementar warm-up navigation                                    │   │
│  │ - Implementar proxy rotation                                        │   │
│  │ - Implementar stealth techniques                                   │   │
│  │ - Implementar rate limiting                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3: IDEALISTA SPIDER                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar IdealistaSpiderNodriver                               │   │
│  │ - Implementar DataDome bypass                                      │   │
│  │ - Testar scraping de Idealista                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 4: IMOVIRTUAL SPIDER                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar ImovirtualSpiderNodriver                              │   │
│  │ - Implementar Cloudflare bypass                                     │   │
│  │ - Testar scraping de Imovirtual                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 5: CASA SAPO SPIDER                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar CasaSapoSpiderNodriver                                │   │
│  │ - Testar scraping de Casa Sapo                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6-7: SPIDER MANAGER                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar SpiderManager                                       │   │
│  │ - Implementar ProxyManager                                         │   │
│  │ - Implementar StealthManager                                        │   │
│  │ - Testar scraping de todos os portais                              │   │
│  │ - Configurar Task Scheduler (Windows)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Semana 2: ETL e Database

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 2: ETL E DATABASE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: DATABASE SCHEMA                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Criar schema SQLite                                                │   │
│  │ - Criar tabelas: raw_listings, clean_listings, valuations, scores│   │
│  │ - Criar índices                                                      │   │
│  │ - Implementar DatabaseRepository                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: NORMALIZER                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar Normalizer                                            │   │
│  │ - Implementar parse_price, parse_area, parse_rooms                    │   │
│  │ - Testar normalização de listings                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3: DEDUPLICATOR                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar Deduplicator                                          │   │
│  │ - Implementar generate_fingerprint                                  │   │
│  │ - Testar deduplicação                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 4: GEOCODER                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar Geocoder                                             │   │
│  │ - Implementar GeocodeCache                                         │   │
│  │ - Implementar geocoding via Nominatim                                │   │
│  │ - Testar geocoding                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 5: ENRICHER E VALIDATOR                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar Enricher (INE data, POIs)                           │   │
│  │ - Implementar Validator                                             │   │
│  │ - Testar enriquecimento e validação                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6-7: PIPELINE ETL                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar PipelineETL                                          │   │
│  │ - Orquestrar Normalizer → Deduplicator → Geocoder → Enricher → Validator│   │
│  │ - Testar pipeline ETL completo                                      │   │
│  │ - Configurar job de ETL no Scheduler                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Semana 3: Valuation e Scoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 3: VALUATION E SCORING                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: HEDONIC MODEL                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar HedonicModel (statsmodels OLS)                        │   │
│  │ - Implementar HedonicFeatures                                       │   │
│  │ - Treinar modelo com dados dummy                                     │   │
│  │ - Testar prediction                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: COMPS ENGINE                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar CompsEngine                                          │   │
│  │ - Implementar find_comparables                                      │   │
│  │ - Implementar adjust_for_differences                                 │   │
│  │ - Testar comps engine                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3: INE CLIENT                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar INEClient                                             │   │
│  │ - Implementar get_freguesia_data                                   │   │
│  │ - Testar cliente INE                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 4: WEIGHTED ENSEMBLE                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar WeightedEnsemble                                     │   │
│  │ - Implementar combine (Hedonic + Comps + INE + XGBoost)             │   │
│  │ - Implementar calculate_confidence                                  │   │
│  │ - Testar ensemble                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 5: SCORE CALCULATORS                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar ScoreDiscountCalculator                              │   │
│  │ - Implementar ScoreLocationCalculator                              │   │
│  │ - Implementar ScoreConditionCalculator                             │   │
│  │ - Implementar ScoreLiquidityCalculator                             │   │
│  │ - Implementar ScoreFreshnessCalculator                              │   │
│  │ - Testar score calculators                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6: RED FLAGS DETECTOR                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar RedFlagsDetector                                    │   │
│  │ - Implementar detect (overpricing, location, condition, etc.)      │   │
│  │ - Testar detector                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 7: SCORING ENGINE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar ScoringEngine                                         │   │
│  │ - Implementar score (combina 5 factores + red flags)                │   │
│  │ - Implementar classificacao                                         │   │
│  │ - Testar scoring engine                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Semana 4: Notification, Dashboard e Scheduler

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 4: NOTIFICATION, DASHBOARD E SCHEDULER             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: TELEGRAM BOT                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Criar Telegram bot via BotFather                                │   │
│  │ - Implementar TelegramBot                                          │   │
│  │ - Implementar send_message, send_photo                              │   │
│  │ - Testar bot                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: MESSAGE FORMATTER                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar MessageFormatter                                      │   │
│  │ - Implementar format_opportunity_message                            │   │
│  │ - Implementar format_summary_message                                │   │
│  │ - Testar formatter                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3: NOTIFICATION ENGINE                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar NotificationEngine                                   │   │
│  │ - Implementar OpportunitySelector                                   │   │
│  │ - Implementar notify_top_opportunities                              │   │
│  │ - Testar notification engine                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 4: DASHBOARD (STREAMLIT)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar app.py                                                 │   │
│  │ - Implementar página Overview                                       │   │
│  │ - Implementar página Search                                          │   │
│  │ - Implementar página Config                                          │   │
│  │ - Testar dashboard                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 5: SCHEDULER (APScheduler)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar SchedulerOrchestrator                                   │   │
│  │ - Configurar AsyncIOScheduler                                     │   │
│  │ - Adicionar jobs (scraping, ETL, valuation, scoring, notification) │   │
│  │ - Testar scheduler                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6: MONITORING                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Implementar HealthChecks                                          │   │
│  │ - Implementar Metrics                                               │   │
│  │ - Implementar AlertManager                                           │   │
│  │ - Configurar logging estruturado                                   │   │
│  │ - Testar monitoring                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 7: INTEGRAÇÃO FINAL                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Integrar todos os componentes                                    │   │
│  │ - Testar pipeline completo (scraping → ETL → valuation → scoring → notification)│   │
│  │ - Configurar Task Scheduler (Windows)                              │   │
│  │ - Testar deployment local                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. FASE 2: VPS PRODUÇÃO (SEMANAS 5-8)

### 4.1 Objectivos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              OBJECTIVOS FASE 2: VPS PRODUÇÃO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FUNCIONAIS:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Migrar para VPS (Ubuntu 22.04)                                    │   │
│  │ - Migrar database para PostgreSQL                                   │   │
│  │ - Configurar Systemd service                                        │   │
│  │ - Configurar Nginx + HTTPS                                        │   │
│  │ - Configurar backup automático                                     │   │
│  │ - Configurar monitoring (Prometheus + Grafana)                     │   │
│  │ - Deployment: VPS (DigitalOcean, Hetzner)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NÃO-FUNCIONAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Uptime 99.5%                                                     │   │
│  │ - SLA 99%                                                           │   │
│  │ - Backup automático                                                 │   │
│  │ - Monitoring 24/7                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tarefas por Semana

#### Semana 5: Preparação VPS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 5: PREPARAÇÃO VPS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: COMPRAR VPS                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Comprar VPS (DigitalOcean, Hetzner, etc.)                        │   │
│  │ - Configurar Ubuntu 22.04 LTS                                       │   │
│  │ - Configurar SSH key                                                │   │
│  │ - Configurar firewall (ufw)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: INSTALAÇÃO DEPENDÊNCIAS                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Instalar Python 3.11+                                             │   │
│  │ - Instalar PostgreSQL 14+                                            │   │
│  │ - Instalar Nginx                                                     │   │
│  │ - Instalar Certbot                                                   │   │
│  │ - Instalar Git                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3: CONFIGURAR POSTGRESQL                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Criar database realestate                                         │   │
│  │ - Criar tabelas (raw_listings, clean_listings, etc.)                 │   │
│  │ - Criar índices                                                      │   │
│  │ - Configurar WAL mode                                                │   │
│  │ - Configurar backup automático                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 4: DEPLOYMENT DO CÓDIGO                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Clonar repositório no VPS                                         │   │
│  │ - Criar virtual environment                                         │   │
│  │ - Instalar dependencies                                            │   │
│  │ - Configurar .env                                                    │   │
│  │ - Testar deployment manual                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 5: CONFIGURAR SYSTEMD                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Criar Systemd service                                           │   │
│  │ - Configurar auto-restart                                          │   │
│  │ - Testar service                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6-7: MIGRAÇÃO DE DADOS                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Exportar SQLite database                                         │   │
│  │ - Importar para PostgreSQL                                         │   │
│  │ - Verificar dados migrados                                          │   │
│  │ - Testar queries em PostgreSQL                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Semana 6: Nginx e HTTPS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEMANA 6: NGINX E HTTPS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 1: CONFIGURAR NGINX                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Instalar Nginx                                                     │   │
│  │ - Configurar reverse proxy                                         │   │
│  │ - Configurar proxy para Streamlit                                   │   │
│  │ - Testar Nginx                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 2: CONFIGURAR CERTBOT                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Instalar Certbot                                                   │   │
│  │ - Obter certificado SSL (Let's Encrypt)                             │   │
│  │ - Configurar auto-renewal                                           │   │
│  │ - Testar HTTPS                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 3-5: MONITORING (PROMETHEUS + GRAFANA)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Instalar Prometheus                                              │   │
│  │ - Instalar Grafana                                                  │   │
│  │ - Configurar metrics do sistema                                     │   │
│  │ - Configurar dashboards                                              │   │
│  │ - Configurar alertas                                                 │   │
│  │ - Testar monitoring                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIA 6-7: CUTOVER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Parar scraping no local                                            │   │
│  │ - Iniciar scraping no VPS                                           │   │
│  │ - Monitorar durante 1 semana                                        │   │
│  │ - Verificar logs e métricas                                         │   │
│  │ - Optimizar se necessário                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. FASE 3: CLOUD-NATIVE (SEMANAS 9-12)

### 5.1 Objectivos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              OBJECTIVOS FASE 3: CLOUD-NATIVE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FUNCIONAIS:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Refactor para microserviços                                      │   │
│  │ - Migrar para Kubernetes                                           │   │
│  │ - Adicionar Redis (cache)                                         │   │
│  │ - Adicionar RabbitMQ (message queue)                              │   │
│  │ - Configurar Celery (task queue)                                   │   │
│  │ - Configurar auto-scaling                                          │   │
│  │ - Configurar HA (multi-zone)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NÃO-FUNCIONAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Horizontal scaling (mais pods)                                   │   │
│  │ - Auto-scaling (baseado em métricas)                              │   │
│  │ - High availability (HA)                                             │   │
│  │ - Uptime 99.9%                                                     │   │
│  │ - SLA 99.9%                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. FASE 4: ENTERPRISE MULTI-REGION (SEMANAS 13-16)

### 6.1 Objectivos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              OBJECTIVOS FASE 4: ENTERPRISE MULTI-REGION                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FUNCIONAIS:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Multi-region deployment                                         │   │
│  │ - Configurar CDN (CloudFront)                                     │   │
│  │ - Configurar multi-master database                                  │   │
│  │ - Configurar global load balancer                                   │   │
│  │ - Configurar disaster recovery                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NÃO-FUNCIONAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Multi-region HA                                                   │   │
│  │ - Disaster recovery automático                                    │   │
│  │ - Global load balancing                                             │   │
│  │ - Uptime 99.99%                                                    │   │
│  │ - SLA 99.99%                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. MILESTONES E DELIVERABLES

### 7.1 Milestones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MILESTONES E DELIVERABLES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MILESTONE 1: MVP LOCAL (Fim da Semana 4)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Deliverable: Sistema completo rodando localmente                 │   │
│  │ - Scraping de 17 portais                                           │   │
│  │ - ETL pipeline                                                     │   │
│  │ - Valuation engine                                                 │   │
│  │ - Scoring engine                                                   │   │
│  │ - Database (SQLite)                                                │   │
│  │ - Dashboard (Streamlit)                                             │   │
│  │ - Scheduler (APScheduler)                                         │   │
│  │ - Notification (Telegram)                                            │   │
│  │ - Deployment: Local (Windows 11)                                  │   │
│  │ Custo: €0/mês                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MILESTONE 2: VPS PRODUÇÃO (Fim da Semana 8)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Deliverable: Sistema rodando em VPS                                │   │
│  │ - Migrado para VPS (Ubuntu 22.04)                                   │   │
│  │ - Database (PostgreSQL)                                              │   │
│  │ - Systemd service                                                  │   │
│  │ - Nginx + HTTPS                                                     │   │
│  │ - Backup automático                                                 │   │
│  │ - Monitoring (Prometheus + Grafana)                                 │   │
│  │ Custo: €20-30/mês                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MILESTONE 3: CLOUD-NATIVE (Fim da Semana 12)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Deliverable: Sistema em Kubernetes                                 │   │
│  │ - Microserviços (scraping, etl, valuation, scoring, notification)    │   │
│  │ - Kubernetes (multi-pods)                                         │   │
│  │ - Redis (cache)                                                     │   │
│  │ - RabbitMQ (message queue)                                         │   │
│  │ - Celery (task queue)                                              │   │
│  │ - Auto-scaling                                                      │   │
│  │ - HA (multi-zone)                                                   │   │
│  │ Custo: €100-200/mês                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MILESTONE 4: ENTERPRISE MULTI-REGION (Fim da Semana 16)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Deliverable: Sistema multi-region                                 │   │
│  │ - Multi-region deployment                                         │   │
│  │ - CDN (CloudFront)                                                 │   │
│  │ - Multi-master database                                            │   │
│  │ - Global load balancer                                             │   │
│  │ - Disaster recovery                                                │   │
│  │ Custo: €500-1000/mês                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DEPENDÊNCIAS ENTRE FASES

### 8.1 Dependências

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DEPENDÊNCIAS ENTRE FASES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 2 DEPENDE DE FASE 1:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Fase 1 deve estar completa e testada                              │   │
│  │ Código deve estar limpo (PEP 8, type hints, docstrings)             │   │
│  │ Testes devem ter coverage ≥70%                                     │   │
│  │ Database deve ter dados suficientes para teste                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3 DEPENDE DE FASE 2:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Fase 2 deve estar estável em produção                             │   │
│  │ Código deve ser refactored para microserviços                      │   │
│  │ Components devem ser stateless (para Kubernetes)                      │   │
│  │ Database deve ser migrado para managed service (RDS)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4 DEPENDE DE FASE 3:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Fase 3 deve estar estável em produção                             │   │
│  │ Kubernetes cluster deve estar configurado                           │   │
│  │ Monitoring deve estar configurado (multi-region)                   │   │
│  │ Disaster recovery deve estar testado                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. RISCOS E MITIGAÇÕES

### 9.1 Riscos e Mitigações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              RISCOS E MITIGAÇÕES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RISCO 1: SCRAPING BLOQUEADO (DATADOME, CLOUDFLARE)                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Usar Nodriver (CDP direct)                                        │   │
│  │ - Usar residential proxies (produção)                               │   │
│  │ - Implementar warm-up navigation                                    │   │
│  │ - Implementar backoff exponencial                                   │   │
│  │ - Implementar circuit breakers                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RISCO 2: DATABASE CORRUPTED                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Backup diário automático                                        │   │
│  │ - Backup offsite (S3, Azure Blob)                                 │   │
│  │ - Testar restore periodicamente                                     │   │
│  │ - WAL mode (para performance)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RISCO 3: PC DESLIGADO (LOCAL DEPLOYMENT)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Configurar auto-restart (Systemd)                                 │   │
│  │ - Monitorar uptime (alertas se PC desligado)                         │   │
│  │ - Migrar para VPS (Fase 2)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RISCO 4: VPS DOWNTIME                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Configurar HA (multi-zone) (Fase 3)                            │   │
│  │ - Configurar auto-scaling                                           │   │
│  │ - Monitorar uptime (alertas)                                       │   │
│  │ - Disaster recovery (Fase 4)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RISCO 5: TELEGRAM TOKEN COMPROMETIDO                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Encriptar token (Fernet)                                         │   │
│  │ - Guardar em .env (não no git)                                    │   │
│  │ - Rotacionar token a cada 90 dias                                   │   │
│  │ - Configurar 2FA no Telegram                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RISCO 6: GDPR VIOLAÇÃO                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mitigação:                                                          │   │
│  │ - Local-first approach (dados ficam local)                         │   │
│  │ - Não guardar dados pessoais intencionalmente                        │   │
│  │ - Logs sem dados pessoais                                           │   │
│  │ - Implementar right to be forgotten                                │   │
│  │ - Data retention 90 dias                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. ESTIMATIVA DE ESFORÇO

### 10.1 Estimativa por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTIMATIVA DE ESFORÇO POR FASE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: MVP LOCAL (4 semanas)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horas: 160-200 horas (40-50 horas/semana)                         │   │
│  │ Recursos: 1 desenvolvedor (full-time)                               │   │
│  │ Custo: €0 (trabalho do próprio)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS PRODUÇÃO (4 semanas)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horas: 80-120 horas (20-30 horas/semana)                           │   │
│  │ Recursos: 1 desenvolvedor (part-time)                               │   │
│  │ Custo: €80-120/mês (desenvolvedor)                                 │   │
│  │ Custo infraestrutura: €20-30/mês                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE (4 semanas)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horas: 160-200 horas (40-50 horas/semana)                         │   │
│  │ Recursos: 1-2 desenvolvedores (full-time)                            │   │
│  │ Custo: €320-400/mês (desenvolvedores)                              │   │
│  │ Custo infraestrutura: €100-200/mês                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: ENTERPRISE MULTI-REGION (4 semanas)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horas: 200-240 horas (50-60 horas/semana)                         │   │
│  │ Recursos: 2-3 desenvolvedores (full-time)                            │   │
│  │ Custo: €640-720/mês (desenvolvedores)                              │   │
│  │ Custo infraestrutura: €500-1000/mês                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOTAL (16 semanas):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horas: 600-760 horas                                              │   │
│  │ Custo desenvolvimento: €1040-1240 (média €65-77/semana)            │   │
│  │ Custo infraestrutura: €0 → €20-30 → €100-200 → €500-1000           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. RECURSOS NECESSÁRIOS

### 11.1 Recursos por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              RECURSOS NECESSÁRIOS POR FASE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: MVP LOCAL                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Desenvolvedor: 1 (Python, SQL, Streamlit)                         │   │
│  │ Hardware: Windows 11 PC (próprio)                                │   │
│  │ Software: Python 3.11+, SQLite, Task Scheduler                     │   │
│  │ Custo: €0                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS PRODUÇÃO                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Desenvolvedor: 1 (Python, PostgreSQL, Nginx, Linux)                 │   │
│  │ Hardware: VPS (2-4 cores, 4-8GB RAM)                              │   │
│  │ Software: Ubuntu 22.04, PostgreSQL 14+, Nginx, Certbot                │   │
│  │ Custo: €20-30/mês (VPS)                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Desenvolvedor: 2 (Python, Kubernetes, Redis, RabbitMQ)             │   │
│  │ Hardware: Kubernetes cluster (3-5 nodes)                            │   │
│  │ Software: Kubernetes, Docker, Redis, RabbitMQ, Celery               │   │
│  │ Custo: €100-200/mês (cloud)                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: ENTERPRISE MULTI-REGION                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Desenvolvedor: 3 (Python, Kubernetes, multi-region, CD)           │   │
│  │ Hardware: Multi-region Kubernetes cluster (5-10 nodes)              │   │
│  │ Software: Kubernetes, Docker, CloudFront, RDS multi-master        │   │
│  │ Custo: €500-1000/mês (cloud)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. CRITÉRIOS DE SUCESSO

### 12.1 Critérios por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CRITÉRIOS DE SUCESSO POR FASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: MVP LOCAL                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Scraping de 17 portais funcionando (60-70% success rate)         │   │
│  │ - ETL pipeline processando 1000 listings/dia                      │   │
│  │ - Valuation engine calculando valor justo                           │   │
│  │ - Scoring engine calculando score 0-10                                │   │
│  │ - Dashboard acessível em localhost:8501                              │   │
│  │ - Scheduler executando jobs automaticamente                         │   │
│  │ - Notification enviando top 3-5 listings/dia                       │   │
│  │ - Test coverage ≥70%                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS PRODUÇÃO                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Sistema rodando 24/7 no VPS                                       │   │
│  │ - Uptime ≥99.5%                                                      │   │
│  │ - HTTPS configurado (SSL/TLS)                                       │   │
│  │ - Backup automático funcionando                                     │   │
│  │ - Monitoring configurado (Prometheus + Grafana)                     │   │
│  │ - Database (PostgreSQL) funcionando                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Microserviços rodando em Kubernetes                              │   │
│  │ - Horizontal scaling (auto-scaling)                                 │   │
│  │ - Redis cache funcionando                                            │   │
│  │ - RabbitMQ message queue funcionando                                │   │
│  │ - Celery task queue funcionando                                      │   │
│  │ - Uptime ≥99.9%                                                     │   │
│  │ - SLA ≥99.9%                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: ENTERPRISE MULTI-REGION                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Multi-region deployment funcionando                                 │   │
│  │ - CDN (CloudFront) funcionando                                       │   │
│  │ - Multi-master database funcionando                                  │   │
│  │ - Global load balancer funcionando                                  │   │
│  │ - Disaster recovery testado                                          │   │
│  │ - Uptime ≥99.99%                                                    │   │
│  │ - SLA ≥99.99%                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. PLANO DE ROLLBACK

### 13.1 Estratégia de Rollback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PLANO DE ROLLBACK                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROLLBACK FASE 2 → FASE 1:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Parar scraping no VPS                                            │   │
│  │ - Retomar scraping no local                                          │   │
│  │ - Exportar PostgreSQL database                                       │   │
│  │ - Importar para SQLite local                                        │   │
│  │ - Reconfigurar Task Scheduler (Windows)                             │   │
│  │ - Monitorar durante 1 semana                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROLLBACK FASE 3 → FASE 2:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Desligar Kubernetes cluster                                      │   │
│  │ - Retomar VPS deployment                                         │   │
│  │ - Migrar database de managed service para VPS                        │   │
│  │ - Reconfigurar Systemd service                                     │   │
│  │ - Monitorar durante 1 semana                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROLLBACK FASE 4 → FASE 3:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Desligar multi-region deployment                                 │   │
│  │ - Retomar single-region Kubernetes                                 │   │
│  │ - Desligar CDN                                                     │   │
│  │ - Reconfigurar single-region load balancer                         │   │
│  │ - Monitorar durante 1 semana                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. COMUNICAÇÃO E REPORTING

### 14.1 Estratégia de Comunicação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIA DE COMUNICAÇÃO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REPORTING SEMANAL:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Progresso da semana (tarefas completas, tarefas pendentes)        │   │
│  │ - Bloqueios e riscos                                                │   │
│  │ - Métricas de performance                                           │   │
│  │ - Próximos passos                                                   │   │
│  │ - Enviar via email ou mensagem                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REPORTING MILESTONE:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Resumo do milestone                                               │   │
│  │ - Deliverables completos                                            │   │
│  │ - Testes e validações                                               │   │
│  │ - Lições aprendidas                                                 │   │
│  │ - Próximos passos                                                   │   │
│  │ - Enviar via email ou mensagem                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ALERTAS CRÍTICAS:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Alerta imediata via Telegram                                     │   │
│  │ - Descrição do problema                                            │   │
│  │ - Impacto estimado                                                  │   │
│  │ - Acção proposta                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE ROADMAP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE ROADMAP                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROADMAP: Roadmap (plano de implementação)                             │
│                                                                             │
│  MILESTONE: Milestone (marco importante)                             │
│                                                                             │
│  DELIVERABLE: Deliverable (resultado entregável)                     │
│                                                                             │
│  FASE: Phase (etapa do roadmap)                                        │
│                                                                             │
│  DEPENDÊNCIA: Dependência (relação entre tarefas/fases)           │
│                                                                             │
│  RISCO: Risco (incerteza que pode afectar o projecto)                │
│                                                                             │
│  MITIGAÇÃO: Mitigação (acção para reduzir risco)                      │
│                                                                             │
│  ESTIMATIVA DE ESFORÇO: Estimativa de esforço (tempo necessário)   │
│                                                                             │
│  RECURSO: Recurso (pessoa, hardware, software)                         │
│                                                                             │
│  CRITÉRIO DE SUCESSO: Critério de sucesso (condição para sucesso)   │
│                                                                             │
│  ROLLBACK: Rollback (reversão para versão anterior)                   │
│                                                                             │
│  REPORTING: Reporting (comunicação de progresso)                       │
│                                                                             │
│  ALERTA: Alerta (notificação de problema)                              │
│                                                                             │
│  BLOQUEIO: Bloqueio (obstáculo que impede progresso)                  │
│                                                                             │
│  SLA: Service Level Agreement (acordo de nível de serviço)           │
│                                                                             │
│  UPTIME: Uptime (tempo de disponibilidade)                           │
│                                                                             │
│  HA: High Availability (alta disponibilidade)                           │
│                                                                             │
│  DOWNTIME: Downtime (tempo de indisponibilidade)                        │
│                                                                             │
│  DISASTER RECOVERY: Disaster recovery (recuperação de desastre)    │
│                                                                             │
│  AUTO-SCALING: Auto-scaling (escala automática)                     │
│                                                                             │
│  HORIZONTAL SCALING: Horizontal scaling (mais máquinas)              │
│                                                                             │
│  VERTICAL SCALING: Vertical scaling (mais recursos)                   │
│                                                                             │
│  LOAD BALANCER: Load balancer (distribuidor de carga)                │
│                                                                             │
│  CDN: Content Delivery Network (rede de distribuição de conteúdo)     │
│                                                                             │
│  MULTI-REGION: Multi-region (deploy em múltiplas regiões)           │
│                                                                             │
│  MULTI-MASTER: Multi-master (múltiplos primários)                       │
│                                                                             │
│  FAILOVER: Failover (recuperação de falha)                             │
│                                                                             │
│  BACKUP: Backup (cópia de segurança)                                   │
│                                                                             │
│  RESTORE: Restore (restauração de backup)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. BASELINE PRODUCTION-READY (ONDA 5)

### 16.1 Ondas 1-5 Completas

**Onda 1: ETL Imports Lazy & Ollama Env-Driven**
- Imports lazy no pipeline ETL para evitar carregar torch/transformers desnecessariamente
- Variável `ENRICH_SKIP_HEAVY` para desabilitar enriquecimento pesado
- Ollama env-driven com warm-up, retry, cache e timeouts separados
- Extras opcionais no requirements.txt para slim install

**Onda 2: Scripts Cross-Platform & .gitignore**
- Criação de `start.sh` (macOS/Linux) com paridade total ao `start.bat` (Windows)
- 10 comandos: install, doctor, api, ui, dashboard, engine, all, test, help, menu
- Criação de `.gitignore` raiz consolidado
- Correção da afirmação errada sobre `realestate_engine/tests/` ser placeholder

**Onda 3: Dark-Mode Fix**
- `.streamlit/config.toml` base alterada para "dark"
- Remoção de cores claras hardcoded em `overview.py` e `scraping_results.py`
- Substituição por variantes dark para melhor contraste e legibilidade

**Onda 4: Scheduler & Notification Hardening**
- APScheduler hardening: `max_instances=1`, `coalesce=True`, `misfire_grace_time`
- Event listeners com logs estruturados `apscheduler.event=`
- `notify_ai_analysis` env-driven (não hardcoda modelo Ollama)
- Fail-closed em `_already_notified_today` (evita spam em outage DB)
- TelegramBot com tratamento de erros específicos (RetryAfter, Forbidden, InvalidToken, BadRequest, TimedOut, NetworkError)

**Onda 5: Documentação Reconciliada**
- Atualização de README.md e realestate_engine/README.md com números reais
- Adição de secção macOS com start.sh, extras opcionais e troubleshooting detalhado
- Remoção de RELATORIO_INCONSISTENCIAS.md (legado)
- Referências ao PRODUCTION_READINESS.md

### 16.2 Estado Atual do Sistema

**Números Reais:**
- 8 portais cobertos por 12 spiders
- 15 views Streamlit
- 53 testes (29 base + 24 production-readiness)
- ~305 testes granulares em `realestate_engine/tests/`
- 4 modelos de valuation + meta-ensemble

### 16.3 Baseline Production-Ready

O sistema atingiu baseline production-ready após a conclusão das Ondas 1-5 de hardening e melhorias. Para escalar o sistema de local para global production-grade, ver `planeamento/21-escala-global-production.md`.

---

*Fim do Documento 18 — Roadmap de Implementação*
