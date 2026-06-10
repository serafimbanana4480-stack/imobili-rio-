# DASHBOARD STREAMLIT PROFISSIONAL — REAL ESTATE OPPORTUNITY ENGINE
## Interface Visual Enterprise-Grade para Análise de Oportunidades Imobiliárias

> **Este documento:** Especificação enterprise-grade do dashboard Streamlit  
> **Objectivo:** Fornecer especificação detalhada de dashboard profissional para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 6.0 (Revisão Profissional — Benchmarking Dashboards Enterprise Real Estate 2025/2026)
> **Benchmarks:** Zillow, Redfin, Idealista Pro, Rentana, CoStar, AirDNA, PropStream

---

## ÍNDICE

1. [Introdução ao Dashboard Profissional](#1-introducao-ao-dashboard-profissional)
2. [Benchmarking Dashboards Enterprise](#2-benchmarking-dashboards-enterprise)
3. [Arquitetura do Dashboard](#3-arquitetura-do-dashboard)
4. [Stack Tecnológico Profissional](#4-stack-tecnologico-profissional)
5. [Design System](#5-design-system)
6. [Estrutura de Views (15 Views)](#6-estrutura-de-views-15-views)
7. [Página: Overview / Command Center](#7-pagina-overview-command-center)
8. [Página: Search & Discovery](#8-pagina-search-discovery)
9. [Página: Listing Detail View](#9-pagina-listing-detail-view)
10. [Página: Comparative Analysis](#10-pagina-comparative-analysis)
11. [Página: Market Intelligence](#11-pagina-market-intelligence)
12. [Página: Investment Analytics](#12-pagina-investment-analytics)
13. [Página: Deal Pipeline & CRM](#13-pagina-deal-pipeline-crm)
14. [Página: Favorites & Watchlist](#14-pagina-favorites-watchlist)
15. [Página: Price Intelligence](#15-pagina-price-intelligence)
16. [Página: Neighborhood Deep Dive](#16-pagina-neighborhood-deep-dive)
17. [Página: Configurações Avançadas](#17-pagina-configuracoes-avancadas)
18. [Página: Telegram & Notificações](#18-pagina-telegram-notificacoes)
19. [Página: System & DevOps](#19-pagina-system-devops)
20. [Página: Data Quality & Diagnostics](#20-pagina-data-quality-diagnostics)
21. [Componentes UI Avançados](#21-componentes-ui-avancados)
22. [Gráficos e Visualizações Enterprise](#22-graficos-e-visualizacoes-enterprise)
23. [Performance & UX](#23-performance-ux)
24. [Deployment & Acessibilidade](#24-deployment-acessibilidade)
25. [Glossário de Dashboard](#25-glossario-de-dashboard)

---

## 1. INTRODUÇÃO AO DASHBOARD PROFISSIONAL

### 1.1 Objectivo do Dashboard

**Dashboard Profissional** é a interface visual enterprise-grade que transforma dados brutos de imóveis em insights acionáveis para tomada de decisão de investimento imobiliário.

**Objectivo:** Fornecer uma experiência comparável às plataformas profissionais (Zillow, Redfin, Idealista Pro, Rentana, CoStar, AirDNA) com:
- **Command Center** com KPIs em tempo real e alerting
- **Análise Comparativa** lado-a-lado de imóveis ( Comparative Market Analysis )
- **Pipeline de Negócios** (CRM lightweight integrado)
- **Watchlist & Favoritos** com alertas inteligentes de redução de preço
- **Market Intelligence** com forecasting e deteção de tendências
- **Investment Analytics** com calculadoras de ROI, yield, cash flow, hipoteca
- **Price Intelligence** com histórico, deteção de reduções, e price drop alerts
- **Neighborhood Scoring** com amenidades (escolas, transporte, segurança)
- **Mobile-First Responsive Design** com Dark Mode
- **Real-time Updates** via polling com indicadores visuais de fresh data

### 1.2 Benchmarking com Dashboards Enterprise

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         BENCHMARKING DASHBOARDS REAL ESTATE PROFISSIONAIS 2025/2026    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ZILLOW / REDFIN (EUA — Consumer + Pro)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Mapa interactivo com heatmap de preços e zonas de interesse     │   │
│  │ ✓ Price history chart (histórico de preços com linha temporal)      │   │
│  │ ✓ Comparable sales (vendas comparáveis lado-a-lado)               │   │
│  │ ✓ Zestimate / Redfin Estimate (valuation automático com intervalo) │   │
│  │ ✓ School ratings integrados (ratings de escolas no mapa)            │   │
│  │ ✓ Walk Score / Transit Score (pontuação de mobilidade)             │   │
│  │ ✓ Favorites & Saved Searches com alertas de novos imóveis           │   │
│  │ ✓ Price drop alerts com percentagem de redução                      │   │
│  │ ✓ Mortgage calculator integrado com amortização                     │   │
│  │ ✓ Rental yield estimation para investidores                         │   │
│  │ ✓ Photo gallery com zoom e navegação                                │   │
│  │ ✓ 3D tours e virtual walkthrough (integração opcional)             │   │
│  │ ✓ Market velocity (dias até venda por zona)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IDEALISTA PRO (Espanha/Portugal — B2B)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Mapa com filtros geográficos avançados (raio, polígono)         │   │
│  │ ✓ Estatísticas de mercado por zona (preço médio, volume, etc.)   │   │
│  │ ✓ Alertas de novos imóveis com filtros avançados                   │   │
│  │ ✓ Export de leads para CRM (CSV, Excel, API)                       │   │
│  │ ✓ Análise de preço por m² com comparáveis                           │   │
│  │ ✓ Histórico de contactos e interacções com cada lead               │   │
│  │ ✓ Dashboard de performance de anúncios                              │   │
│  │ ✓ Report generation automático (PDF, email)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RENTANA / YARDI (Enterprise Multifamily)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Portfolio Dashboard (multi-property performance view)              │   │
│  │ ✓ Revenue Intelligence (rent pricing optimization AI)                │   │
│  │ ✓ Occupancy & Vacancy Tracking com forecasting                      │   │
│  │ ✓ Lease Renewal & Retention Dashboard com scoring                   │   │
│  │ ✓ Investment & NOI Performance (cap rate, IRR, cash-on-cash)        │   │
│  │ ✓ Market & Competitive Analysis (comparables, concessions)           │   │
│  │ ✓ Predictive Analytics & Forecasting (demand, pricing)               │   │
│  │ ✓ Reporting & Analytics Automation (scheduled reports)              │   │
│  │ ✓ Tenant Screening & Risk Scoring                                    │   │
│  │ ✓ Maintenance & Work Order Tracking                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AIRDNA (Short-term Rental Analytics)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Rental Yield Calculator com ocupação estimada                     │   │
│  │ ✓ Occupancy Rate Analytics por zona e seasonality                   │   │
│  │ ✓ Revenue Estimation com comparação mercado                         │   │
│  │ ✓ Seasonality Analysis (high/low season identification)             │   │
│  │ ✓ Competitive Set Analysis (Airbnb vs Booking vs direct)             │   │
│  │ ✓ Market Grade Scoring (A-F por zona)                               │   │
│  │ ✓ Review Sentiment Analysis                                         │   │
│  │ ✓ Future Booking Demand Prediction                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROPSTREAM / BATCHDATA (Investment Intelligence)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Property Intelligence (owner data, liens, foreclosure history)    │   │
│  │ ✓ Contact Enrichment (skip tracing, phone, email)                    │   │
│  │ ✓ Market Trends & Analytics (trending neighborhoods)              │   │
│  │ ✓ Comp Analysis (sold comps, active comps, off-market)             │   │
│  │ ✓ List Management & Campaigns (direct mail, skip tracing)            │   │
│  │ ✓ Real-time Data Updates com notificações push                      │   │
│  │ ✓ Flip Calculator (ARV, rehab cost, profit estimation)             │   │
│  │ ✓ Rental Calculator (rent, expenses, cash flow)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Diferenciais do Real Estate Opportunity Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         DIFERENCIAIS DO REAL ESTATE OPPORTUNITY ENGINE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SCORE DE OPORTUNIDADE (0-10) — ÚNICO NO MERCADO                        │
│     - Algoritmo proprietário combinando 5 factores + red flags            │
│     - Discount Score (preço vs valor justo)                                │
│     - Location Score (freguesia, proximidade metro, escolas)                │
│     - Condition Score (estado de conservação, ano construção)               │
│     - Liquidity Score (tempo no mercado, volume de transacções)           │
│     - Freshness Score (idade do anúncio, data de publicação)                │
│     - Red Flags (overpricing, localização problemática, anúncio suspeito)   │
│     - NÃO existe em nenhuma plataforma comercial atualmente                │
│                                                                             │
│  2. VALUATION MULTI-CAMADA                                                 │
│     - Hedonic Model (statsmodels OLS) — valor base por características     │
│     - Comps Engine (comparáveis reais) — valor por similaridade            │
│     - INE Macro Data (dados oficiais portugueses) — valor por região        │
│     - XGBoost Ensemble — valor por machine learning                        │
│     - Weighted Ensemble com intervalo de confiança                          │
│     - SHAP explainability (porquê este valor?)                             │
│                                                                             │
│  3. PIPELINE DE NEGÓCIOS INTEGRADO (CRM LIGHTWEIGHT)                       │
│     - Detectado → Contactado → Visitado → Proposta → Negociação → Fechado │
│     - Notas por imóvel                                                     │
│     - Documentos anexados (fotos, contratos, relatórios)                    │
│     - Calendar integration (lembretes de visitas)                         │
│     - Route planning (planeamento de rotas para visitas múltiplas)         │
│                                                                             │
│  4. ALERTAS INTELIGENTES MULTI-CANAL                                       │
│     - Telegram Bot com notificações push                                   │
│     - Price Drop Alerts (quando preço desce X%)                            │
│     - New Opportunity Alerts (novos imóveis com score ≥ Y)                  │
│     - Market Shift Alerts (quando tendência de mercado muda)                │
│     - Configurable thresholds por utilizador                                │
│                                                                             │
│  5. ANÁLISE DE MERCADO PORTUGUÊS COM DADOS INE                             │
│     - Preço médio por m² por freguesia (dados INE oficiais)               │
│     - Evolução anual trimestral                                             │
│     - Comparação inter-freguesias                                           │
│     - Focus em Porto (expansível para Lisboa, Braga, Aveiro, Coimbra)      │
│                                                                             │
│  6. LOCAL-FIRST & PRIVACY-BY-DESIGN                                        │
│     - Todos os dados ficam localmente no PC do utilizador                   │
│     - Sem subscrições mensais (vs €200-500/mês das alternativas)            │
│     - GDPR compliant por design (dados nunca saem do dispositivo)           │
│     - Open source (código auditável)                                       │
│                                                                             │
│  7. SCRAPING MULTI-PORTAL EM TEMPO REAL                                     │
│     - 8 portais em simultâneo (Idealista, Imovirtual, Casa Sapo, OLX,     │
│       ERA, Century21, SuperCasa, REMAX)                                     │
│     - Agregação e deduplicação automática                                   │
│     - Dados frescos (atualização a cada 30 minutos)                        │
│     - Anti-bot bypass com Nodriver CDP                                     │
│                                                                             │
│  8. PREDICTIVE ANALYTICS & FORECASTING                                     │
│     - Forecasting de preços com XGBoost (próximos 6-12 meses)             │
│     - Detecção de tendências de mercado (bull/bear signals)                │
│     - Seasonality analysis (melhor época para comprar/vender)             │
│     - Market velocity prediction (tempo estimado até venda)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ARQUITECTURA DO DASHBOARD ENTERPRISE

### 2.1 Arquitectura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DO DASHBOARD ENTERPRISE (4 CAMADAS)            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CAMADA 1: APRESENTAÇÃO (STREAMLIT)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Multi-page App (st.navigation) — 15 views                         │  │ │
│  │ - Theme Engine (Light/Dark/System) via st.session_state           │   │
│  │ - Responsive Layout (desktop, tablet, mobile breakpoints)         │   │
│  │ - Real-time Updates (st.rerun com polling de 30s)                 │   │
│  │ - State Management (st.session_state — filtros, favoritos, etc.)  │   │
│  │ - URL State Sharing (query params para partilha de pesquisas)     │   │
│  │ - Keyboard Shortcuts (Ctrl+K search, Ctrl+D dark mode, etc.)      │   │
│  │ - Onboarding Tour (st.dialog para primeiro acesso)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CAMADA 2: COMPONENTES UI                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - KPI Cards (métricas com sparklines, deltas, tendências)         │   │
│  │ - Data Grids (st.dataframe com sorting, filtering, pagination)   │   │
│  │   → MVP: st.dataframe nativo                                     │   │
│  │   → Pro: streamlit-aggrid para sorting/filtering avançado          │   │
│  │ - Interactive Charts (Plotly — zoom, pan, brush, lasso select)    │   │
│  │ - Map Components (Folium + streamlit-folium + heatmap layer)      │   │
│  │   → Pro: pydeck para mapas 3D e layers avançados                   │   │
│  │ - Form Components (inputs validados com feedback em tempo real)    │   │
│  │ - Modal / Dialog (st.dialog para detalhes de listing)               │   │
│  │ - Toast Notifications (st.toast para feedback não-intrusivo)      │   │
│  │ - Progress Indicators (st.progress, st.spinner, skeleton loaders)  │   │
│  │ - Tabs, Accordions, Columns, Sidebar (layout avançado)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CAMADA 3: DADOS CACHED                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - st.cache_data(ttl=300s) — dados em tempo real                   │   │
│  │ - st.cache_data(ttl=3600s) — dados de mercado (INE, histórico)    │   │
│  │ - st.cache_resource — conexões database, modelos ML               │   │
│  │ - Database Repository (SQLAlchemy ORM — SQLite/PostgreSQL)        │   │
│  │ - Query Builder (filtros dinâmicos SQL com parametrização)        │   │
│  │ - Async Data Loading (threading para queries pesadas)              │   │
│  │ - DataFrames (pandas com vectorização para performance)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CAMADA 4: BACKEND & PERSISTÊNCIA                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - FastAPI Endpoints (health, metrics, data — /api/v1/*)           │   │
│  │ - WebSocket Server (updates push para dashboard em tempo real)     │   │
│  │ - REST API (queries complexas, agregações, exports)               │   │
│  │ - Authentication (JWT tokens — opcional para multi-user)           │   │
│  │ - Rate Limiting (proteção contra abuse)                              │   │
│  │ - SQLite/PostgreSQL (dados estruturados)                           │   │
│  │ - Redis (cache distribuído — opcional para produção)               │   │
│  │ - File System (exports CSV, PDF, Excel, imagens)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ARQUITECTURA DO DASHBOARD

### 3.1 Stack Completo (MVP → Enterprise)

```python
# requirements.txt — MVP Tier
streamlit==1.42.0          # Framework dashboard (multi-page, dialogs, fragments)
pandas==2.2.0              # Data manipulation e analytics
plotly==5.22.0             # Interactive charts (zoom, pan, lasso, brush)
folium==0.16.0             # Interactive maps (OpenStreetMap)
streamlit-folium==0.18.0   # Streamlit integration para Folium
sqlalchemy==2.0.25         # ORM para SQLite/PostgreSQL
python-dotenv==1.0.0       # Environment variables
loguru==0.7.2              # Structured logging (dashboard logs viewer)

# requirements.txt — Pro Tier (adicionais)
streamlit-aggrid==1.0.5    # Advanced data grid (sorting, filtering, grouping)
streamlit-extras==0.4.0    # Extra components (metric cards, toggles, etc.)
pydeck==0.9.1              # 3D maps e layers avançados (Deck.gl)
altair==5.3.0              # Declarative viz (para gráficos estáticos rápidos)
streamlit-plotly-events==0.0.6  # Event handling em Plotly charts

# requirements.txt — Enterprise Tier (adicionais)
fastapi==0.115.0           # API backend para queries pesadas
uvicorn==0.30.0            # ASGI server
httpx==0.27.0              # Async HTTP client para API calls
websockets==12.0           # Real-time updates push
reportlab==4.2.0           # PDF report generation
openpyxl==3.1.2            # Excel export avançado
pillow==10.3.0             # Image processing (thumbnails, galleries)
```

### 3.2 Justificação Técnica por Componente

**Streamlit (v1.42+):**
- Multi-page nativo (`st.navigation`) — sem hacks
- Dialogs/Modals nativos (`st.dialog`) — para detalhes de listings
- Fragments (`st.fragment`) — atualizações parciais de UI sem rerun completo
- Session State — persistência de filtros, favoritos, estado da UI
- Native theming (Light/Dark/System) — sem CSS hacks
- Cache primitives (`st.cache_data`, `st.cache_resource`) — performance
- Cache invalidation manual — force refresh de dados
- `st.rerun` — programmatic refresh para real-time updates
- `st.toast` — notificações não-intrusivas
- `st.status` — indicadores de progresso para operações longas
- `st.html` — embed de HTML customizado quando necessário
- **Porquê:** Desenvolvimento 10x mais rápido que React/Vue para data apps

**Plotly (v5.22+):**
- Zoom, pan, box/lasso select, multi-axis, subplots
- 40+ chart types (candlestick, waterfall, sunburst, treemap, sankey)
- Export nativo (PNG, SVG, PDF) via toolbar
- Annotations, shapes, reference lines, trendlines
- Event callbacks (click, hover, select) para interacção avançada
- Animated transitions entre estados de dados
- **Porquê:** Melhor interacção do que Matplotlib/Seaborn para dashboards

**Folium + PyDeck:**
- Folium: Mapas 2D com markers, popups, clusters, heatmaps (simples)
- PyDeck: Mapas 3D, layers GPU-acelerados, hexagon layers, scatterplot layers
- **Porquê:** PyDeck para heatmaps densos de preços; Folium para navegação simples

**Streamlit-AGGrid (Pro):**
- Sorting, filtering, grouping, pivoting em tabelas
- Row selection multipla (para bulk operations)
- Cell editing inline (para CRM notes)
- Export CSV/Excel direto da grid
- **Porquê:** `st.dataframe` é limitado; AGGrid é essencial para tabelas complexas

**FastAPI (Enterprise):**
- Endpoints para queries pesadas (evita bloqueio do Streamlit)
- WebSocket para push de updates em tempo real
- Background tasks para exports longos (PDF, Excel)
- **Porquê:** Streamlit é single-threaded; FastAPI descarrega trabalho pesado

---

## 4. DESIGN SYSTEM

### 4.1 Cores e Temas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DESIGN SYSTEM — CORES E TEMAS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LIGHT THEME (Default)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Primary:    #1E88E5 (Azul Material) — links, botões primários     │   │
│  │ Secondary:  #43A047 (Verde) — sucesso, score alto, crescimento    │   │
│  │ Warning:    #FB8C00 (Laranja) — alertas, score médio              │   │
│  │ Danger:     #E53935 (Vermelho) — erros, score baixo, red flags    │   │
│  │ Info:       #00ACC1 (Ciano) — info, status, metadados             │   │
│  │ Background: #FAFAFA (Cinza muito claro) — fundo da app            │   │
│  │ Surface:    #FFFFFF (Branco) — cards, tabelas, modals            │   │
│  │ Text:       #212121 (Preto quase) — texto principal              │   │
│  │ Muted:      #757575 (Cinza) — labels, descrições, timestamps      │   │
│  │ Border:     #E0E0E0 (Cinza claro) — bordas, divisores              │   │
│  │ Chart 1:    #1E88E5 │ Chart 2: #43A047 │ Chart 3: #FB8C00        │   │
│  │ Chart 4:    #E53935 │ Chart 5: #8E24AA │ Chart 6: #00ACC1        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DARK THEME                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Primary:    #42A5F5 (Azul claro) — links, botões primários         │   │
│  │ Secondary:  #66BB6A (Verde claro) — sucesso, score alto            │   │
│  │ Warning:    #FFA726 (Laranja claro) — alertas, score médio         │   │
│  │ Danger:     #EF5350 (Vermelho claro) — erros, score baixo        │   │
│  │ Background: #121212 (Preto Material) — fundo da app               │   │
│  │ Surface:    #1E1E1E (Cinza escuro) — cards, tabelas, modals     │   │
│  │ Text:       #FFFFFF (Branco) — texto principal                    │   │
│  │ Muted:      #B0B0B0 (Cinza claro) — labels, descrições            │   │
│  │ Border:     #333333 (Cinza médio) — bordas, divisores             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCORE COLOR SCALE (Consistente em ambos os temas)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 0.0-3.9:  🔴 Vermelho — Fraco (avoid)                              │   │
│  │ 4.0-5.9:  🟡 Amarelo/Laranja — Médio (caution)                    │   │
│  │ 6.0-7.9:  🟢 Verde claro — Bom (consider)                        │   │
│  │ 8.0-8.9:  🟢 Verde — Muito Bom (strong consider)                   │   │
│  │ 9.0-10.0: 💚 Verde escuro/Cyan — Imperdível (act immediately)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DISCOUNT COLOR SCALE                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 0-5%:    🔴 Vermelho — Sem discount / Overpriced                    │   │
│  │ 5-10%:   🟡 Amarelo — Discount modesto                              │   │
│  │ 10-20%:  🟢 Verde — Bom discount                                    │   │
│  │ 20-30%:  💚 Verde escuro — Excelente discount                      │   │
│  │ 30%+:    🌟 Cyan/Dourado — Oportunidade excepcional                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tipografia e Espaçamento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              TIPOGRAFIA E ESPAÇAMENTO                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIPOGRAFIA (Streamlit nativo — não customizável sem CSS)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Títulos:    st.header() — 24px, bold                                │   │
│  │ Subtitles:  st.subheader() — 20px, semibold                        │   │
│  │ Body:       st.write() / st.markdown() — 16px, regular            │   │
│  │ Captions:   st.caption() — 12px, muted                            │   │
│  │ Metrics:    st.metric() — 28px value, 14px label                   │   │
│  │ Code:       st.code() — monospace 14px                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ESPAÇAMENTO                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ st.divider() — separação entre secções                              │   │
│  │ st.columns() — 2-4 colunas para KPIs, 1 coluna para detalhes      │   │
│  │ st.tabs() — agrupamento de conteúdo relacionado                    │   │
│  │ st.expander() — conteúdo colapsável (detalhes, logs)              │   │
│  │ st.container() — grouping lógico de elementos                      │   │
│  │ st.empty() — placeholder para lazy loading                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LAYOUT RESPONSIVO (Breakpoints implícitos do Streamlit)                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Desktop (≥1024px):  3-4 colunas, sidebar expandida                  │   │
│  │ Tablet (768-1024px): 2 colunas, sidebar colapsada                   │   │
│  │ Mobile (<768px):    1 coluna, sidebar como overlay                │   │
│  │ Streamlit lida com isto automaticamente via CSS flexbox           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. ESTRUTURA DE VIEWS (15 VIEWS)

### 5.1 Navigation Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              NAVIGATION HIERARCHY — 15 VIEWS ENTERPRISE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY NAVIGATION (Sidebar — sempre visível)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🏠 Overview / Command Center — KPIs, top opportunities, alertas   │   │
│  │ 🔍 Search & Discovery — Pesquisa avançada, filtros, resultados     │   │
│  │ ⭐ Favorites & Watchlist — Favoritos, watchlist, price alerts    │   │
│  │ 📊 Market Intelligence — Análise de mercado, forecasting, trends  │   │
│  │ 💰 Investment Analytics — ROI, yield, cash flow, mortgage calc    │   │
│  │ 📈 Price Intelligence — Price history, drops, comparables, velocity   │   │
│  │ 🗺️ Neighborhood Deep Dive — Amenidades, escolas, transporte, safety │   │
│  │ 📋 Deal Pipeline & CRM — Pipeline, notas, documentos, calendar   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SECONDARY NAVIGATION (Sidebar — collapsible "Admin" section)           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ⚙️ Configurações Avançadas — Telegram, thresholds, scraping, API   │   │
│  │ 📱 Telegram & Notificações — Histórico, estatísticas, testes      │   │
│  │ 🖥️ System & DevOps — Status, logs, performance, health checks      │   │
│  │ 🔍 Data Quality & Diagnostics — Quality score, erros, reparos    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HIDDEN / CONTEXTUAL PAGES (acessíveis via click, não no sidebar)          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 Listing Detail View — Página detalhe de cada imóvel (dialog)    │   │
│  │ ⚖️ Comparative Analysis — Comparação lado-a-lado de 2-4 listings  │   │
│  │ 🖼️ Photo Gallery — Galeria de fotos com zoom e navegação          │   │
│  │ 📝 PDF Report Generator — Relatório PDF profissional de listing    │   │
│  │ 📅 Calendar & Visits — Agenda de visitas com route planning        │   │
│  │ 📊 Custom Dashboard Builder — Drag-and-drop widgets (futuro)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Page Routing (Streamlit Multi-page)

```python
# .streamlit/pages.toml (ou app.py com st.navigation)
# Estrutura de directórios:
#
# dashboard/
# ├── app.py                    # Entry point + sidebar + routing
# ├── pages/
# │   ├── 01_overview.py        # 🏠 Overview / Command Center
# │   ├── 02_search.py          # 🔍 Search & Discovery
# │   ├── 03_favorites.py        # ⭐ Favorites & Watchlist
# │   ├── 04_market_intel.py     # 📊 Market Intelligence
# │   ├── 05_investment.py       # 💰 Investment Analytics
# │   ├── 06_price_intel.py      # 📈 Price Intelligence
# │   ├── 07_neighborhood.py     # 🗺️ Neighborhood Deep Dive
# │   ├── 08_deal_pipeline.py    # 📋 Deal Pipeline & CRM
# │   ├── 09_config.py           # ⚙️ Configurações Avançadas
# │   ├── 10_telegram.py         # 📱 Telegram & Notificações
# │   ├── 11_system.py           # 🖥️ System & DevOps
# │   ├── 12_data_quality.py     # 🔍 Data Quality & Diagnostics
# │   └── __init__.py
# ├── components/                # Reusable UI components
# │   ├── __init__.py
# │   ├── kpi_card.py           # KPI card com sparkline
# │   ├── listing_card.py        # Card de listing (compact view)
# │   ├── score_badge.py         # Badge de score com cor
# │   ├── price_history_chart.py # Chart de histórico de preços
# │   ├── map_viewer.py          # Componente de mapa
# │   └── filter_panel.py        # Painel de filtros reutilizável
# ├── dialogs/                   # Modal dialogs (st.dialog)
# │   ├── __init__.py
# │   ├── listing_detail.py      # Detalhe de listing (rich modal)
# │   ├── compare_listings.py    # Comparative analysis modal
# │   ├── photo_gallery.py       # Photo gallery modal
# │   └── pdf_preview.py         # PDF preview modal
# └── utils/
#     ├── __init__.py
#     ├── theme.py               # Theme management (light/dark)
#     ├── data_loader.py         # Async data loading com caching
#     └── state_manager.py       # Session state persistence
```

---

## 7. PÁGINA: OVERVIEW / COMMAND CENTER

### 7.1 Descrição

**Command Center** é a página principal que fornece um "single pane of glass" com todos os KPIs críticos, oportunidades de topo, alertas activos e visualizações de alto nível. Inspirado em dashboards enterprise (Tableau, PowerBI, Grafana).

**Objectivo:** Dar ao utilizador uma visão instantânea do estado do mercado e das melhores oportunidades em < 3 segundos.

### 7.2 Layout da Página

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🏠 COMMAND CENTER — Real Estate Opportunity Engine                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: REAL-TIME KPI BAR (4-6 métricas em cards)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Total   │ │ Active  │ │ Avg     │ │ Imperdí-│ │ Avg     │ │ Last    │   │
│  │Listings │ │ Listings│ │ Score   │ │ véis    │ │ Discount│ │Scrape   │   │
│  │ 5,234   │ │ 4,891   │ │ 4.72    │ │ 127     │ │ 8.4%    │ │ 2m ago  │   │
│  │ ▲ +123  │ │ ▲ +98   │ │ ▲ +0.2  │ │ ▲ +12   │ │ ▲ +1.2% │ │ ▼ -3m   │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                                             │
│  ROW 2: ALERTS & NOTIFICATIONS BAR (scrollable, dismissable)                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🚨 3 novos "Imperdíveis" desde última visita | 🔥 Price drop: T3    │   │
│  │ Cedofeita -25% → €180k | 📈 Mercado Paranhos subiu 3.2% este mês   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROW 3: TWO-COLUMN LAYOUT                                                   │
│  ┌────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ TOP 10 OPPORTUNITIES       │  │ MARKET SNAPSHOT                      │   │
│  │ (score ≥ 8.0)              │  │                                     │   │
│  │                            │  │ • Score Distribution (donut chart)  │   │
│  │ #1 T3 Cedofeita    9.2 ⭐  │  │ • Price vs Value Scatter (Plotly)   │   │
│  │ #2 T2 Paranhos     8.7 ⭐  │  │ • Avg Price by Freguesia (bar)      │   │
│  │ #3 T4 Bonfim       8.5 ⭐  │  │ • New Listings Timeline (area)      │   │
│  │ #4 T3 Baixa        8.3 ⭐  │  │                                     │   │
│  │ #5 T2 Vitória      8.1 ⭐  │  │                                     │   │
│  │    [Ver todos →]          │  │                                     │   │
│  └────────────────────────────┘  └─────────────────────────────────────┘   │
│                                                                             │
│  ROW 4: INTERACTIVE MAP (full width)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🗺️ MAPA DE OPORTUNIDADES (heatmap de scores + markers)              │   │
│  │ - Cluster markers por densidade                                      │   │
│  │ - Color coding: verde = score alto, vermelho = score baixo          │   │
│  │ - Click em marker → abre Listing Detail Dialog                       │   │
│  │ - Filter overlay: score ≥ X, price ≤ Y, freguesia Z                  │   │
│  │ - Heatmap layer: preço/m² por zona (from INE data)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROW 5: PIPELINE STATUS & QUICK ACTIONS                                    │
│  ┌────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ DEAL PIPELINE MINI-VIEW    │  │ QUICK ACTIONS                        │   │
│  │ Detected: 45 | Contacted:12│  │ [🔍 Search] [⭐ Favorites] [📊 Market] │   │
│  │ Visited: 8 | Proposal: 3   │  │ [📈 Price Intel] [🗺️ Map] [⚙️ Config] │   │
│  │ Closed: 1                  │  │ [📥 Export Top 10] [📤 Share]        │   │
│  └────────────────────────────┘  └─────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Implementação Completa (Overview / Command Center)

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from components.kpi_card import render_kpi_card
from components.score_badge import render_score_badge
from components.listing_card import render_listing_card
from dialogs.listing_detail import show_listing_detail
from utils.data_loader import load_cached_data

st.set_page_config(
    page_title="Command Center | RE Opportunity Engine",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.header("🏠 Command Center")
st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')} | Próxima scrape: em 18 minutos")

# ────────────────────────────────────────────────────────────────────────────
# ROW 1: REAL-TIME KPI BAR
# ────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)  # Cache de 1 minuto para KPIs
def get_kpi_data():
    return {
        'total_listings': 5234,
        'active_listings': 4891,
        'avg_score': 4.72,
        'imperdiveis': 127,
        'avg_discount': 8.4,
        'last_scrape_minutes': 2,
        'delta_total': 123,
        'delta_active': 98,
        'delta_score': 0.2,
        'delta_imperdiveis': 12,
        'delta_discount': 1.2,
        'delta_scrape': -3
    }

kpis = get_kpi_data()

cols = st.columns(6)
kpi_definitions = [
    ('Total Listings', kpis['total_listings'], kpis['delta_total'], '#1E88E5'),
    ('Active Listings', kpis['active_listings'], kpis['delta_active'], '#00ACC1'),
    ('Avg Score', f"{kpis['avg_score']:.2f}", kpis['delta_score'], '#43A047'),
    ('Imperdíveis', kpis['imperdiveis'], kpis['delta_imperdiveis'], '#8E24AA'),
    ('Avg Discount', f"{kpis['avg_discount']:.1f}%", kpis['delta_discount'], '#FB8C00'),
    ('Last Scrape', f"{kpis['last_scrape_minutes']}m ago", kpis['delta_scrape'], '#757575')
]

for col, (label, value, delta, color) in zip(cols, kpi_definitions):
    with col:
        st.metric(
            label=label,
            value=value,
            delta=delta,
            delta_color="normal" if delta >= 0 else "inverse"
        )

# ────────────────────────────────────────────────────────────────────────────
# ROW 2: ALERTS BAR (condicional — só aparece se houver alertas)
# ────────────────────────────────────────────────────────────────────────────

alerts = [
    {"type": "imperdivel", "msg": "🚨 3 novos 'Imperdíveis' (score ≥ 9.0) desde a última visita", "priority": "high"},
    {"type": "price_drop", "msg": "🔥 Price drop detectado: T3 Cedofeita de €240k → €180k (-25%)", "priority": "high"},
    {"type": "market_shift", "msg": "📈 Mercado Paranhos: preço médio subiu 3.2% vs mês passado", "priority": "info"}
]

if alerts:
    with st.container(border=True):
        alert_cols = st.columns(len(alerts))
        for col, alert in zip(alert_cols, alerts):
            with col:
                if alert["priority"] == "high":
                    st.error(alert["msg"], icon="🚨")
                elif alert["priority"] == "medium":
                    st.warning(alert["msg"], icon="⚠️")
                else:
                    st.info(alert["msg"], icon="ℹ️")

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# ROW 3: TOP OPPORTUNITIES + MARKET SNAPSHOT
# ────────────────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([0.45, 0.55])

with left_col:
    st.subheader("🏆 Top 10 Opportunities")
    
    @st.cache_data(ttl=300)
    def get_top_opportunities():
        return pd.DataFrame({
            'id': ['L001', 'L002', 'L003', 'L004', 'L005'],
            'titulo': ['T3 Renovado Cedofeita', 'T2 Moderno Paranhos', 
                      'T4 Bonfim Centro', 'T3 Novo Baixa', 'T2 Vitória'],
            'preco': [180000, 210000, 195000, 320000, 175000],
            'valor_justo': [240000, 260000, 235000, 370000, 205000],
            'area': [85, 65, 95, 110, 60],
            'freguesia': ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória'],
            'score': [9.2, 8.7, 8.5, 8.3, 8.1],
            'discount': [25.0, 19.2, 17.0, 13.5, 14.6],
            'url': ['https://...'] * 5
        })
    
    top_df = get_top_opportunities()
    
    # Render each listing as a compact card
    for _, row in top_df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.5, 0.2, 0.15, 0.15])
            with c1:
                st.markdown(f"**{row['titulo']}** — {row['freguesia']}")
                st.caption(f"€{row['preco']:,.0f} | {row['area']}m² | Valor justo: €{row['valor_justo']:,.0f}")
            with c2:
                st.markdown(f"**{row['discount']:.1f}%** discount")
            with c3:
                render_score_badge(row['score'])
            with c4:
                if st.button("👁️ Ver", key=f"view_{row['id']}"):
                    show_listing_detail(row['id'])
    
    st.link_button("Ver todas as oportunidades →", "/Search", use_container_width=True)

with right_col:
    st.subheader("📊 Market Snapshot")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Scores", "Preços", "Freguesias", "Timeline"])
    
    with tab1:
        # Donut chart — score distribution
        score_data = pd.DataFrame({
            'classificacao': ['Imperdível\n(9-10)', 'Muito Bom\n(8-8.9)', 'Bom\n(7-7.9)', 
                            'Aceitável\n(6-6.9)', 'Fraco\n(<6)'],
            'total': [45, 82, 310, 890, 3907],
            'color': ['#8E24AA', '#43A047', '#66BB6A', '#FB8C00', '#E53935']
        })
        fig = go.Figure(data=[go.Pie(
            labels=score_data['classificacao'],
            values=score_data['total'],
            hole=0.55,
            marker_colors=score_data['color'],
            textinfo='label+percent',
            textposition='outside'
        )])
        fig.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            annotations=[dict(text='Scores', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True, height=300)
    
    with tab2:
        # Scatter: Price vs Value Justo
        scatter_data = pd.DataFrame({
            'preco': [180000, 210000, 195000, 320000, 175000, 150000, 280000, 190000],
            'valor_justo': [240000, 260000, 235000, 370000, 205000, 180000, 310000, 220000],
            'score': [9.2, 8.7, 8.5, 8.3, 8.1, 7.5, 7.2, 6.8],
            'area': [85, 65, 95, 110, 60, 55, 80, 70]
        })
        fig = px.scatter(
            scatter_data, x='valor_justo', y='preco',
            size='area', color='score',
            color_continuous_scale=['#E53935', '#FB8C00', '#43A047', '#8E24AA'],
            range_color=[0, 10],
            labels={'valor_justo': 'Valor Justo (€)', 'preco': 'Preço Pedido (€)'},
            title="Preço vs Valor Justo (tamanho = área)"
        )
        fig.add_shape(type='line', x0=0, y0=0, x1=400000, y1=400000,
                     line=dict(dash='dash', color='gray'))
        st.plotly_chart(fig, use_container_width=True, height=300)
    
    with tab3:
        # Bar chart: avg price by freguesia
        freguesia_prices = pd.DataFrame({
            'freguesia': ['Baixa', 'Vitória', 'Cedofeita', 'Bonfim', 'Paranhos', 'Massarelos'],
            'preco_m2': [3100, 2900, 2800, 2700, 2600, 2500]
        })
        fig = px.bar(freguesia_prices, x='freguesia', y='preco_m2',
                    color='preco_m2', color_continuous_scale='Blues',
                    labels={'preco_m2': '€/m²'}, title="Preço Médio por m² por Freguesia")
        st.plotly_chart(fig, use_container_width=True, height=300)
    
    with tab4:
        # Area chart: new listings over time
        timeline = pd.DataFrame({
            'date': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'new_listings': [45, 52, 38, 61, 55, 42, 39, 48, 53, 44,
                           51, 47, 56, 49, 43, 58, 41, 50, 46, 54,
                           40, 48, 52, 45, 57, 42, 50, 48, 55, 51]
        })
        fig = px.area(timeline, x='date', y='new_listings',
                     labels={'new_listings': 'Novos Listings'},
                     title="Novos Listings (últimos 30 dias)")
        fig.update_traces(fill='tozeroy', line_color='#1E88E5')
        st.plotly_chart(fig, use_container_width=True, height=300)

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# ROW 4: INTERACTIVE MAP (full width)
# ────────────────────────────────────────────────────────────────────────────

st.subheader("🗺️ Mapa de Oportunidades")

map_tab1, map_tab2 = st.tabs(["Heatmap de Scores", "Heatmap Preço/m² (INE)"])

with map_tab1:
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import MarkerCluster, HeatMap
    
    m = folium.Map(location=[41.15, -8.61], zoom_start=13, tiles='CartoDB positron')
    
    # Heatmap layer (score density)
    heat_data = [[41.15, -8.61, 9.2], [41.16, -8.60, 8.7], [41.14, -8.59, 8.5],
                 [41.14, -8.62, 8.3], [41.15, -8.60, 8.1]]
    HeatMap(heat_data, radius=25, blur=15, max_zoom=13).add_to(m)
    
    # Clustered markers for high-score listings
    mc = MarkerCluster()
    for _, row in top_df.iterrows():
        color = 'green' if row['score'] >= 8 else 'orange' if row['score'] >= 6 else 'red'
        folium.Marker(
            location=[41.15 + hash(row['id']) % 100 / 1000, 
                     -8.61 + hash(row['id'][::-1]) % 100 / 1000],
            popup=f"<b>{row['titulo']}</b><br>€{row['preco']:,.0f} | Score: {row['score']}",
            tooltip=f"Score: {row['score']} | Discount: {row['discount']:.1f}%",
            icon=folium.Icon(color=color, icon='home', prefix='fa')
        ).add_to(mc)
    mc.add_to(m)
    
    st_folium(m, use_container_width=True, height=500)
    
    # Map filters overlay
    map_filter_cols = st.columns(4)
    with map_filter_cols[0]:
        map_score_min = st.slider("Score mínimo", 0.0, 10.0, 7.0, key="map_score")
    with map_filter_cols[1]:
        map_price_max = st.number_input("Preço máx (€)", 50000, 1000000, 500000, key="map_price")
    with map_filter_cols[2]:
        map_freguesias = st.multiselect("Freguesias", 
            ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória', 'Massarelos'],
            ['Cedofeita', 'Paranhos'], key="map_freg")
    with map_filter_cols[3]:
        st.button("🔄 Aplicar Filtros", use_container_width=True)

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# ROW 5: PIPELINE MINI-VIEW + QUICK ACTIONS
# ────────────────────────────────────────────────────────────────────────────

pipe_col, action_col = st.columns([0.6, 0.4])

with pipe_col:
    st.subheader("📋 Deal Pipeline (últimos 30 dias)")
    
    pipeline_data = pd.DataFrame({
        'stage': ['Detectado', 'Contactado', 'Visitado', 'Proposta', 'Negociação', 'Fechado'],
        'count': [45, 12, 8, 3, 2, 1],
        'value': [0, 0, 0, 0, 0, 180000]
    })
    
    fig = px.funnel(pipeline_data, x='count', y='stage',
                   color='count', color_continuous_scale='Blues',
                   title="Pipeline de Oportunidades")
    st.plotly_chart(fig, use_container_width=True, height=250)

with action_col:
    st.subheader("⚡ Quick Actions")
    
    action_buttons = [
        ("🔍 Search", "Pesquisar imóveis"),
        ("⭐ Favorites", "Ver favoritos"),
        ("📊 Market", "Análise de mercado"),
        ("📈 Price Intel", "Inteligência de preços"),
        ("🗺️ Map", "Mapa completo"),
        ("⚙️ Config", "Configurações")
    ]
    
    btn_cols = st.columns(2)
    for i, (icon_label, help_text) in enumerate(action_buttons):
        with btn_cols[i % 2]:
            st.button(icon_label, help=help_text, use_container_width=True)
    
    st.divider()
    st.download_button(
        "📥 Export Top 10 (CSV)",
        top_df.to_csv(index=False).encode('utf-8'),
        "top_opportunities.csv",
        "text/csv",
        use_container_width=True
    )
```

---

## 8. PÁGINA: SEARCH & DISCOVERY

### 8.1 Descrição

**Search & Discovery** é a página de pesquisa avançada com filtros multi-critério, resultados em data grid profissional (AGGrid), visualização em mapa integrado, e exportação de dados. Inspirado na experiência de pesquisa do Zillow, Idealista e Redfin.

**Objectivo:** Permitir ao utilizador encontrar imóveis que correspondam aos seus critérios de investimento em segundos, com visualizações ricas e acções em massa.

### 7.2 Layout da Página

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔍 SEARCH & DISCOVERY — Real Estate Opportunity Engine                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ FILTERS BAR (collapsible, com saved searches)                        │   │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │ │Preço    │ │Área     │ │Quartos  │ │Score    │ │Freguesia│         │   │
│  │ │50k-500k │ │50-200m² │ │2-4      │ │≥ 7.0    │ │[Cedof..]│         │   │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │ │Estado   │ │Tipo     │ │Discount │ │Freshness│ │Advanced │         │   │
│  │ │[Renova] │ │[T2,T3]  │ │≥ 10%   │ │< 7 dias │ │[🔽]    │         │   │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  │ [💾 Save Search] [🔖 Load Search] [🔄 Reset] [📤 Export Results]    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────┐  ┌───────────────────────────────────┐ │
│  │ RESULTS (AGGrid / DataFrame)   │  │ MAP VIEW (Folium / PyDeck)        │ │
│  │                                │  │                                   │ │
│  │ □ Score | Title | Price | Area│  │    [🗺️ Interactive Map]           │ │
│  │ □ 9.2  | T3 Cedofeita | €180k │  │    Click marker → highlight row   │ │
│  │ □ 8.7  | T2 Paranhos  | €210k │  │    Row hover → highlight marker     │ │
│  │ □ 8.5  | T4 Bonfim    | €195k │  │                                   │ │
│  │ □ ...  | ...           | ...  │  │                                   │ │
│  │                                │  │                                   │ │
│  │ [1] [2] [3] ... [15] (1456)  │  │                                   │ │
│  │                                │  │                                   │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ BULK ACTIONS (quando ≥1 row selecionada):                          │   │
│  │ [⭐ Add to Favorites] [📊 Compare Selected (2-4)] [📥 Export CSV]   │   │
│  │ [📋 Add to Pipeline] [🔔 Set Price Alert] [📤 Share Link]            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Implementação

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.header("🔍 Search & Discovery")
st.caption("Encontre oportunidades com filtros avançados e visualização em mapa")

# ────────────────────────────────────────────────────────────────────────────
# SAVED SEARCHES
# ────────────────────────────────────────────────────────────────────────────

if "saved_searches" not in st.session_state:
    st.session_state.saved_searches = {
        "Oportunidades Cedofeita": {"freguesias": ["Cedofeita"], "score_min": 7.0, "discount_min": 10},
        "T2-3 até €250k": {"tipos": ["T2", "T3"], "preco_max": 250000, "score_min": 6.0},
        "Renovados Baixa": {"freguesias": ["Baixa"], "estado": ["Renovado"], "score_min": 7.5}
    }

saved_search = st.selectbox("🔖 Saved Searches", 
    ["— Nova Pesquisa —"] + list(st.session_state.saved_searches.keys()))

if saved_search != "— Nova Pesquisa —":
    params = st.session_state.saved_searches[saved_search]
    st.success(f"Loaded: {saved_search}")
else:
    params = {}

# ────────────────────────────────────────────────────────────────────────────
# FILTERS BAR
# ────────────────────────────────────────────────────────────────────────────

with st.expander("🔍 Filtros Avançados", expanded=True):
    f1, f2, f3, f4, f5 = st.columns(5)
    
    with f1:
        preco_range = st.slider("Preço (€)", 0, 1000000, 
            (params.get("preco_min", 50000), params.get("preco_max", 500000)),
            step=10000)
    with f2:
        area_range = st.slider("Área (m²)", 0, 500,
            (params.get("area_min", 50), params.get("area_max", 200)),
            step=5)
    with f3:
        quartos_range = st.select_slider("Quartos", options=[0,1,2,3,4,5,6],
            value=(params.get("quartos_min", 1), params.get("quartos_max", 4)))
    with f4:
        score_min = st.slider("Score mínimo", 0.0, 10.0,
            params.get("score_min", 5.0), step=0.5)
    with f5:
        freguesias = st.multiselect("Freguesias",
            ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória', 'Massarelos', 'Santo Ildefonso'],
            default=params.get("freguesias", []))
    
    f6, f7, f8, f9, f10 = st.columns(5)
    with f6:
        estados = st.multiselect("Estado",
            ['Novo', 'Renovado', 'Bom estado', 'Necessita obras'],
            default=params.get("estado", []))
    with f7:
        tipos = st.multiselect("Tipologia",
            ['T0', 'T1', 'T2', 'T3', 'T4', 'T5+'],
            default=params.get("tipos", ['T2', 'T3', 'T4']))
    with f8:
        discount_min = st.slider("Discount mínimo (%)", 0, 50,
            params.get("discount_min", 0), step=5)
    with f9:
        freshness_max = st.slider("Idade máx. anúncio (dias)", 1, 90, 30)
    with f10:
        cert_energetico = st.multiselect("Cert. Energético",
            ['A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G'],
            default=['A+', 'A', 'B', 'C'])

# Action bar
act1, act2, act3, act4 = st.columns([1, 1, 1, 2])
with act1:
    if st.button("💾 Save Search", use_container_width=True):
        search_name = st.text_input("Nome da pesquisa")
        if search_name:
            st.session_state.saved_searches[search_name] = {
                "preco_min": preco_range[0], "preco_max": preco_range[1],
                "area_min": area_range[0], "area_max": area_range[1],
                "score_min": score_min, "freguesias": freguesias,
                "discount_min": discount_min
            }
            st.toast(f"Pesquisa '{search_name}' guardada!")
with act2:
    if st.button("🔄 Reset", use_container_width=True):
        st.rerun()
with act3:
    if st.button("📤 Export", use_container_width=True):
        st.info("Export funcionalidade — ver Data Export")
with act4:
    result_count_placeholder = st.empty()

# ────────────────────────────────────────────────────────────────────────────
# RESULTS + MAP
# ────────────────────────────────────────────────────────────────────────────

results_col, map_col = st.columns([0.55, 0.45])

with results_col:
    @st.cache_data(ttl=300)
    def search_listings(filters):
        # Query database com filtros dinâmicos
        return pd.DataFrame({
            'id': ['L001', 'L002', 'L003', 'L004', 'L005'],
            'titulo': ['T3 Renovado Cedofeita', 'T2 Moderno Paranhos', 
                      'T4 Bonfim Centro', 'T3 Novo Baixa', 'T2 Vitória'],
            'preco': [180000, 210000, 195000, 320000, 175000],
            'area': [85, 65, 95, 110, 60],
            'quartos': [3, 2, 4, 3, 2],
            'freguesia': ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória'],
            'score': [9.2, 8.7, 8.5, 8.3, 8.1],
            'discount': [25.0, 19.2, 17.0, 13.5, 14.6],
            'estado': ['Renovado', 'Moderno', 'Centro', 'Novo', 'Bom estado'],
            'idade_anuncio_dias': [2, 5, 1, 7, 3]
        })
    
    filters = {
        'preco_range': preco_range, 'area_range': area_range,
        'score_min': score_min, 'freguesias': freguesias,
        'discount_min': discount_min, 'freshness_max': freshness_max
    }
    
    results_df = search_listings(filters)
    result_count_placeholder.markdown(f"**{len(results_df)}** resultados encontrados")
    
    # AGGrid ou st.dataframe com configuração avançada
    st.dataframe(
        results_df[['score', 'titulo', 'preco', 'area', 'quartos', 'freguesia', 'discount', 'idade_anuncio_dias']],
        column_config={
            'score': st.column_config.ProgressColumn("Score", format="%.1f", min_value=0, max_value=10),
            'preco': st.column_config.NumberColumn("Preço", format="€%d", step=1000),
            'discount': st.column_config.ProgressColumn("Discount", format="%.1f%%", min_value=0, max_value=50),
            'idade_anuncio_dias': st.column_config.NumberColumn("Dias", help="Idade do anúncio")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Bulk actions
    if len(results_df) > 0:
        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            st.button("⭐ Favoritos", use_container_width=True)
        with b2:
            st.button("⚖️ Comparar", use_container_width=True)
        with b3:
            st.button("📋 Pipeline", use_container_width=True)
        with b4:
            st.button("🔔 Alerta", use_container_width=True)
        with b5:
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSV", csv, "search_results.csv", "text/csv", 
                             use_container_width=True)

with map_col:
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import MarkerCluster
    
    m = folium.Map(location=[41.15, -8.61], zoom_start=13, tiles='CartoDB positron')
    mc = MarkerCluster()
    
    for _, row in results_df.iterrows():
        color = 'green' if row['score'] >= 8 else 'orange' if row['score'] >= 6 else 'red'
        folium.Marker(
            location=[41.15 + hash(row['id']) % 100 / 1000, 
                     -8.61 + hash(row['id'][::-1]) % 100 / 1000],
            popup=f"<b>{row['titulo']}</b><br>€{row['preco']:,.0f} | Score: {row['score']}",
            icon=folium.Icon(color=color, icon='home', prefix='fa')
        ).add_to(mc)
    mc.add_to(m)
    
    st_folium(m, use_container_width=True, height=500)
```

---

## 9. PÁGINA: LISTING DETAIL VIEW (MODAL)

### 9.1 Descrição

**Listing Detail View** é um modal/dialog que mostra detalhes completos de um imóvel quando clicado em Search, Overview ou Map. Inspirado no modal de detalhes do Zillow e Idealista.

**Objectivo:** Fornecer uma visão completa de um listing sem sair da página actual, com todas as informações necessárias para decisão de investimento.

### 9.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📄 LISTING DETAIL — T3 Renovado Cedofeita                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: HEADER + SCORE BADGE                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ T3 Renovado Cedofeita | €180k | 85m² | 3 quartos                   │   │
│  │ Score: 9.2 ⭐⭐⭐⭐⭐ | Discount: 25% | Imperdível                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABS: [Info] [Valuation] [Score] [Mapa] [History] [Comparáveis]           │
│                                                                             │
│  TAB: INFO                                                                  │
│  - Fotos (galeria)                                                          │
│  - Descrição completa                                                       │
│  - Características (quartos, wcs, garagem, varanda, etc.)                  │
│  - Certificado energético                                                   │
│  - Anunciante e contacto                                                     │
│                                                                             │
│  TAB: VALUATION                                                            │
│  - Valor justo estimado: €240k                                             │
│  - Preço pedido: €180k                                                      │
│  - Discount: 25%                                                            │
│  - Breakdown por camada (Hedonic, Comps, INE, XGB)                         │
│  - Confidence interval: €220k-€260k (90% CI)                               │
│                                                                             │
│  ACTION BUTTONS: [⭐ Favorito] [📋 Pipeline] [🔔 Alerta] [📤 Share]         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Implementação

```python
import streamlit as st

@st.dialog("Listing Detail", width="large")
def show_listing_detail(listing_id):
    listing = get_listing_by_id(listing_id)
    
    st.markdown(f"### {listing['titulo']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Preço", f"€{listing['preco']:,.0f}")
    col2.metric("Score", f"{listing['score']:.1f}")
    col3.metric("Discount", f"{listing['discount']:.1f}%")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Info", "Valuation", "Score", "Mapa", "History"])
    
    with tab1:
        st.image(listing['fotos'])
        st.markdown(listing['descricao'])
    
    with tab2:
        st.metric("Valor Justo", f"€{listing['valor_justo']:,.0f}")
        st.metric("Discount", f"{listing['discount']:.1f}%")
```

---

## 10. PÁGINA: COMPARATIVE ANALYSIS (MODAL)

### 10.1 Descrição

**Comparative Analysis** é um modal que permite comparar 2-4 listings lado-a-lado. Inspirado no comparador do Idealista e Redfin.

**Objectivo:** Facilitar a comparação objectiva de múltiplos imóveis para decisão de investimento.

### 10.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚖️ COMPARATIVE ANALYSIS — 3 Listings Selecionados                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COMPARISON TABLE                                                           │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐              │
│  │ Feature      │ T3 Cedofeita │ T2 Paranhos  │ T4 Bonfim    │              │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤              │
│  │ Preço        │ €180k        │ €210k        │ €195k        │              │
│  │ Área         │ 85m²         │ 65m²         │ 95m²         │              │
│  │ Preço/m²     │ €2,118       │ €3,231       │ €2,053       │              │
│  │ Score        │ 9.2 ⭐⭐⭐⭐⭐ │ 8.7 ⭐⭐⭐⭐  │ 8.5 ⭐⭐⭐⭐  │              │
│  │ Discount     │ 25%          │ 19%          │ 17%          │              │
│  └──────────────┴──────────────┴──────────────┴──────────────┘              │
│                                                                             │
│  🏆 BEST VALUE: T3 Cedofeita — maior área, menor preço/m², score alto       │
│                                                                             │
│  RADAR CHART: Scores em 5 dimensões (discount, location, condition, liquidity, freshness)
│                                                                             │
│  MAPA: Todos os 3 listings marcados no mapa                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Implementação

```python
@st.dialog("Comparative Analysis", width="large")
def show_compare_modal(listing_ids):
    listings = [get_listing_by_id(id) for id in listing_ids]
    
    # Create comparison table
    compare_data = {
        'Feature': ['Preço', 'Área', 'Preço/m²', 'Score', 'Discount'],
        **{l['titulo']: [l['preco'], l['area'], l['preco']/l['area'], l['score'], l['discount']] for l in listings}
    }
    st.dataframe(pd.DataFrame(compare_data))
    
    # Highlight best value
    best = min(listings, key=lambda x: x['preco']/x['area'])
    st.success(f"🏆 Best Value: {best['titulo']} — menor preço/m²")
```

---

## 11. PÁGINA: MARKET INTELLIGENCE

### 11.1 Descrição

**Market Intelligence** é a página de análise avançada de mercado com dados INE, forecasting de preços, seasonality analysis, detecção de tendências (bull/bear signals) e comparação entre freguesias. Inspirado em Zillow Research, Idealista Trends e AirDNA Market Intelligence.

### 11.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 MARKET INTELLIGENCE — Porto, Portugal                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: MARKET KPIs                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Preço/m² │ │Δ Anual  │ │Listings │ │Velocity │ │Sentiment│              │
│  │ €2,850  │ │ +8.4% ▲│ │ 4,891  │ │ 45 dias│ │ Bullish │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  ROW 2: TABS — [Price Trends] [Forecasting] [Seasonality] [Compare Zones] │
│                                                                             │
│  TAB: PRICE TRENDS                                                         │
│  ┌────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Price/m² por Freguesia (Line)  │  │ Price Heatmap (Freg × Typology)│  │
│  │ 2022 → 2023 → 2024 → 2025     │  │ T1│T2│T3│T4│T5               │  │
│  └────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Implementação

*Ver secção 10.3 do documento original para implementação completa.*

---

## 12. PÁGINA: INVESTMENT ANALYTICS

### 12.1 Descrição

**Investment Analytics** é a página com calculadoras de ROI, yield, cash flow, hipoteca, cap rate, IRR e amortization schedule. Inspirado nas calculadoras do BiggerPockets e Mashvisor.

**Objectivo:** Fornecer ferramentas de análise financeira para avaliar rentabilidade de investimentos imobiliários.

### 12.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  💰 INVESTMENT ANALYTICS — Calculadoras Financeiras                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUTS (defaults do Config):                                               │
│  Preço Compra: €180k | Down Payment: 20% | Interest Rate: 3.5% | Loan: 30a │
│  Renda Estimada: €800/mês | Expenses: €200/mês | Tax Bracket: 28%            │
│                                                                             │
│  TABS: [ROI Calculator] [Cash Flow] [Mortgage] [Cap Rate] [IRR] [Amortization]
│                                                                             │
│  TAB: ROI CALCULATOR                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                          │
│  │Cash-on-Cash│ROI Total│Payback  │Net Yield │                          │
│  │  8.5%   │  12.3%  │  11.8a  │  5.3%   │                          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Implementação

```python
st.header("💰 Investment Analytics")
with st.sidebar:
    price = st.number_input("Preço Compra (€)", value=180000, step=10000)
    down_pct = st.slider("Down Payment (%)", 0, 100, 20)
    rate = st.slider("Taxa Juro (%)", 0.5, 10.0, 3.5, 0.1)
    term = st.selectbox("Prazo (anos)", [15,20,25,30], index=2)
    rent = st.number_input("Renda (€)", value=800, step=50)
    expenses = st.number_input("Despesas (€)", value=200, step=25)

down = price * down_pct / 100
loan = price - down
n = term * 12
mr = rate / 100 / 12
payment = loan * (mr*(1+mr)**n)/((1+mr)**n-1) if rate > 0 else loan/n
noi = (rent - expenses) * 12
cash_on_cash = (noi - payment*12) / down * 100 if down > 0 else 0
cap_rate = noi / price * 100

st.metric("Cash-on-Cash", f"{cash_on_cash:.1f}%")
st.metric("Cap Rate", f"{cap_rate:.1f}%")
st.metric("Prestação", f"€{payment:,.0f}")

score = min(10, max(0, cash_on_cash/2 + cap_rate/2))
st.progress(score/10)
st.markdown(f"**Score: {score:.1f}/10**")
```

---

## 13. PÁGINA: DEAL PIPELINE & CRM

### 13.1 Descrição

**Deal Pipeline & CRM** é a página com kanban board de 5 stages, notas por imóvel, documentos anexados, calendar de visitas e route planner. Inspirado no HubSpot e Pipedrive.

**Objectivo:** Gerir o pipeline de deals desde detecção até fecho.

### 13.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📋 DEAL PIPELINE & CRM — Gestão de Oportunidades                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KANBAN BOARD (5 stages):                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Detected  │Contacted │Visited   │Proposal  │Closed    │          │
│  │  45      │   12     │    8     │    3     │    1     │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                             │
│  TABS: [Pipeline] [Notes] [Documents] [Calendar] [Route Planner]            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.3 Implementação

```python
st.header("📋 Deal Pipeline & CRM")

# Kanban stages
stages = ["Detected", "Contacted", "Visited", "Proposal", "Closed"]
colors = ["#6c757d", "#ffc107", "#17a2b8", "#fd7e14", "#28a745"]

# Sample pipeline data
pipeline_data = {
    "Detected": [{"id": 1, "title": "T3 Cedofeita", "price": 195000, "score": 8.2}],
    "Contacted": [{"id": 2, "title": "T2 Vitória", "price": 175000, "score": 7.5}],
    "Visited": [{"id": 3, "title": "T4 Boavista", "price": 280000, "score": 9.1}],
    "Proposal": [{"id": 4, "title": "T1 Bonfim", "price": 135000, "score": 6.8}],
    "Closed": [{"id": 5, "title": "T2 Campanhã", "price": 160000, "score": 7.9}]
}

# Kanban board
cols = st.columns(len(stages))
for i, stage in enumerate(stages):
    with cols[i]:
        st.markdown(f"<div style='background:{colors[i]};padding:10px;border-radius:5px;text-align:center;color:white;'><b>{stage}</b></div>", unsafe_allow_html=True)
        count = len(pipeline_data.get(stage, []))
        st.caption(f"{count} deals")
        for deal in pipeline_data.get(stage, []):
            with st.container():
                st.markdown(f"**{deal['title']}**")
                st.markdown(f"€{deal['price']:,.0f} | Score: {deal['score']}")
                st.button(f"Mover →", key=f"move_{deal['id']}")

# Tabs for details
t1, t2, t3, t4 = st.tabs(["📝 Notas", "📄 Documentos", "📅 Calendário", "🗺️ Route Planner"])

with t1:
    st.subheader("Notas por Imóvel")
    selected_deal = st.selectbox("Selecionar Deal", [d['title'] for stage in pipeline_data.values() for d in stage])
    note = st.text_area("Nova Nota", placeholder="Escreva notas sobre este imóvel...")
    if st.button("Guardar Nota"):
        st.success("Nota guardada!")
    st.markdown("**Histórico:**")
    st.markdown("- 2024-01-15: Primeiro contacto com o agente")
    st.markdown("- 2024-01-18: Visita agendada para sábado")

with t2:
    st.subheader("Documentos")
    uploaded = st.file_uploader("Anexar Documento", type=["pdf", "doc", "docx", "jpg", "png"])
    if uploaded:
        st.success(f"Ficheiro {uploaded.name} carregado!")
    st.markdown("**Documentos existentes:**")
    st.markdown("- 📄 Contrato de compra (PDF)")
    st.markdown("- 📸 Fotos da visita (ZIP)")
    st.markdown("- 📊 Avaliação bancária (PDF)")

with t3:
    st.subheader("Calendário de Visitas")
    visit_date = st.date_input("Data da Visita")
    visit_time = st.time_input("Hora da Visita")
    visit_notes = st.text_input("Notas da Visita")
    if st.button("Agendar Visita"):
        st.success(f"Visita agendada para {visit_date} às {visit_time}")

with t4:
    st.subheader("Route Planner")
    st.markdown("Planeie rotas para visitar múltiplos imóveis no mesmo dia")
    selected_visits = st.multiselect("Selecionar imóveis para visitar", 
                                     [d['title'] for stage in pipeline_data.values() for d in stage])
    if selected_visits:
        st.info(f"Rota otimizada: {' → '.join(selected_visits)}")
        st.metric("Distância Total Estimada", "12.5 km")
        st.metric("Tempo Total Estimado", "45 min")
```

---

## 14. PÁGINA: FAVORITES & WATCHLIST

### 14.1 Descrição

**Favorites & Watchlist** é a página com lista de favoritos, price alerts configurados, watchlist e tags personalizadas. Inspirado nos favoritos do Zillow e watchlists do Idealista.

**Objectivo:** Guardar e monitorizar imóveis de interesse.

### 14.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⭐ FAVORITES & WATCHLIST — Imóveis Guardados                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FAVORITES LIST (cards com foto, preço, score):                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                      │
│  │ T3 Cedofeita │ T2 Paranhos  │ T4 Bonfim    │                      │
│  │ €180k | 9.2  │ €210k | 8.7  │ €195k | 8.5  │                      │
│  │ [⭐] [📋] [🔔]│ [⭐] [📋] [🔔]│ [⭐] [📋] [🔔]│                      │
│  └──────────────┘ └──────────────┘ └──────────────┘                      │
│                                                                             │
│  WATCHLIST (alertas quando condições mudam):                                 │
│  - T3 Cedofeita: alertar se preço < €170k ou score > 9.5                   │
│  - T2 Paranhos: alertar se discount > 25%                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.3 Implementação

```python
st.header("⭐ Favorites & Watchlist")

# Sample favorites data
favorites = [
    {"id": 1, "title": "T3 Cedofeita", "price": 195000, "old_price": 210000, "score": 8.2, "date_added": "2024-01-10", "tags": ["oportunidade", "centro"]},
    {"id": 2, "title": "T2 Vitória", "price": 175000, "old_price": 175000, "score": 7.5, "date_added": "2024-01-12", "tags": ["renovado"]},
    {"id": 3, "title": "T4 Boavista", "price": 280000, "old_price": 295000, "score": 9.1, "date_added": "2024-01-15", "tags": ["luxo", "garagem"]}
]

# Price alerts
st.subheader("🔔 Price Alerts")
alert_col1, alert_col2, alert_col3 = st.columns(3)
with alert_col1:
    st.metric("Alertas Ativos", "5")
with alert_col2:
    st.metric("Reduções Detetadas", "2", "-€35k total")
with alert_col3:
    st.metric("Novos Imóveis", "8", "+3 esta semana")

# Favorites table
st.subheader("⭐ Meus Favoritos")
for fav in favorites:
    price_drop = fav['old_price'] - fav['price']
    price_drop_pct = (price_drop / fav['old_price'] * 100) if fav['old_price'] > 0 else 0
    
    with st.container():
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
        with c1:
            st.markdown(f"**{fav['title']}**")
            st.caption(f"Adicionado: {fav['date_added']}")
        with c2:
            st.markdown(f"€{fav['price']:,.0f}")
            if price_drop > 0:
                st.markdown(f"<span style='color:green'>↓ €{price_drop:,.0f} ({price_drop_pct:.1f}%)</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"Score: **{fav['score']}/10**")
        with c4:
            st.markdown(" ".join([f"`{t}`" for t in fav['tags']]))
        with c5:
            st.button("🗑️ Remover", key=f"rem_{fav['id']}")
            st.button("📊 Comparar", key=f"comp_{fav['id']}")

# Watchlist configuration
st.subheader("⚙️ Configurar Alertas")
with st.form("alert_config"):
    st.selectbox("Tipo de Alerta", ["Redução de Preço", "Novo Imóvel na Zona", "Score > 8", "Preço < Média Mercado"])
    st.slider("Threshold de Redução (%)", 1, 50, 10)
    st.multiselect("Zonas a Monitorizar", ["Cedofeita", "Boavista", "Campanhã", "Bonfim", "Vitória"])
    st.form_submit_button("Guardar Alerta")

# Tags management
st.subheader("🏷️ Tags Personalizadas")
tags = ["oportunidade", "centro", "renovado", "luxo", "garagem", "terraço", "investimento"]
selected_tags = st.multiselect("Filtrar por Tags", tags)
if selected_tags:
    st.info(f"A filtrar por: {', '.join(selected_tags)}")
```

---

## 15. PÁGINA: PRICE INTELLIGENCE

### 15.1 Descrição

**Price Intelligence** é a página com price history por listing, price drop detection, market velocity, price per m² benchmarking e overpricing alerts. Inspirado no Price History do Zillow e Price Drops do Redfin.

**Objectivo:** Analisar tendências de preços e detectar oportunidades de valorização.

### 15.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📈 PRICE INTELLIGENCE — Tendências de Preços                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRICE DROP ALERTS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔥 T3 Cedofeita: €195k → €180k (-7.7% em 7 dias)                    │   │
│  │ 🔥 T2 Vitória: €190k → €175k (-7.9% em 3 dias)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABS: [Price History] [Price Drops] [Velocity] [Benchmarking]           │
│                                                                             │
│  TAB: PRICE HISTORY (line chart por listing)                                │
│  TAB: VELOCITY (scatter: price vs days on market)                            │
│  TAB: BENCHMARKING (price/m² por freguesia)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.3 Implementação

```python
st.header("📊 Price Intelligence")

import plotly.graph_objects as go
import pandas as pd

# Sample price history data
price_history = [
    {"date": "2023-06-01", "price": 210000, "event": "Listado"},
    {"date": "2023-07-15", "price": 205000, "event": "Price Drop"},
    {"date": "2023-09-01", "price": 200000, "event": "Price Drop"},
    {"date": "2023-10-20", "price": 195000, "event": "Price Drop"},
    {"date": "2023-11-15", "price": 195000, "event": "Stable"},
    {"date": "2023-12-01", "price": 190000, "event": "Price Drop"},
    {"date": "2024-01-10", "price": 190000, "event": "Current"}
]

df = pd.DataFrame(price_history)
df['date'] = pd.to_datetime(df['date'])

# Price history chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['price'], mode='lines+markers', name='Preço',
                         line=dict(color='blue', width=3), marker=dict(size=10)))
fig.update_layout(title="Histórico de Preços", xaxis_title="Data", yaxis_title="Preço (€)")
st.plotly_chart(fig, use_container_width=True)

# Price metrics
col1, col2, col3, col4 = st.columns(4)
initial_price = price_history[0]['price']
current_price = price_history[-1]['price']
total_drop = initial_price - current_price
total_drop_pct = (total_drop / initial_price) * 100
days_on_market = (df['date'].iloc[-1] - df['date'].iloc[0]).days

with col1:
    st.metric("Preço Atual", f"€{current_price:,.0f}")
with col2:
    st.metric("Redução Total", f"€{total_drop:,.0f}", f"-{total_drop_pct:.1f}%")
with col3:
    st.metric("Dias no Mercado", f"{days_on_market} dias")
with col4:
    st.metric("Avg Drop/Month", f"€{total_drop/max(1,days_on_market*30):,.0f}")

# Price drop detection
st.subheader("🔍 Price Drop Detection")
drops = []
for i in range(1, len(price_history)):
    if price_history[i]['price'] < price_history[i-1]['price']:
        drop_amount = price_history[i-1]['price'] - price_history[i]['price']
        drop_pct = (drop_amount / price_history[i-1]['price']) * 100
        drops.append({"date": price_history[i]['date'], "amount": drop_amount, "pct": drop_pct})

if drops:
    drops_df = pd.DataFrame(drops)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=drops_df['date'], y=drops_df['pct'], marker_color='red', name='Redução %'))
    fig2.update_layout(title="Reduções de Preço", xaxis_title="Data", yaxis_title="Redução (%)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Sem reduções de preço detetadas.")

# Price per m² benchmarking
st.subheader("📐 Price per m² Benchmarking")
sample_data = [
    {"listing": "T3 Cedofeita", "price": 195000, "area": 85, "price_m2": 2294, "type": "listado"},
    {"listing": "T3 Média Zona", "price": 210000, "area": 90, "price_m2": 2333, "type": "média"},
    {"listing": "T3 Mínimo", "price": 175000, "area": 80, "price_m2": 2188, "type": "mínimo"},
    {"listing": "T3 Máximo", "price": 250000, "area": 100, "price_m2": 2500, "type": "máximo"}
]

bench_df = pd.DataFrame(sample_data)
fig3 = go.Figure()
colors = ['blue' if t == 'listado' else 'gray' for t in bench_df['type']]
fig3.add_trace(go.Bar(x=bench_df['listing'], y=bench_df['price_m2'], marker_color=colors))
fig3.update_layout(title="Preço por m² - Benchmarking", xaxis_title="Imóvel", yaxis_title="€/m²")
st.plotly_chart(fig3, use_container_width=True)

# Market velocity
st.subheader("⚡ Market Velocity")
velocity_data = {
    "Zona": ["Cedofeita", "Boavista", "Campanhã", "Bonfim", "Vitória"],
    "Avg Days": [45, 32, 67, 55, 28],
    "Sales/Month": [12, 18, 8, 10, 22]
}
vel_df = pd.DataFrame(velocity_data)
col_v1, col_v2 = st.columns(2)
with col_v1:
    fig4 = go.Figure(go.Bar(x=vel_df['Zona'], y=vel_df['Avg Days'], marker_color='orange'))
    fig4.update_layout(title="Dias Médios até Venda", xaxis_title="Zona", yaxis_title="Dias")
    st.plotly_chart(fig4, use_container_width=True)
with col_v2:
    fig5 = go.Figure(go.Bar(x=vel_df['Zona'], y=vel_df['Sales/Month'], marker_color='green'))
    fig5.update_layout(title="Vendas por Mês", xaxis_title="Zona", yaxis_title="Vendas")
    st.plotly_chart(fig5, use_container_width=True)

# Overpricing alerts
st.subheader("⚠️ Overpricing Alerts")
st.warning("3 imóveis estão 15%+ acima da média da zona")
overpriced = [
    {"title": "T2 Boavista", "price": 320000, "avg_zone": 280000, "premium": 14.3},
    {"title": "T1 Cedofeita", "price": 185000, "avg_zone": 160000, "premium": 15.6},
    {"title": "T4 Campanhã", "price": 350000, "avg_zone": 300000, "premium": 16.7}
]
for op in overpriced:
    st.markdown(f"- **{op['title']}**: €{op['price']:,.0f} (média zona: €{op['avg_zone']:,.0f}) — **+{op['premium']:.1f}%**")
```

---

## 16. PÁGINA: NEIGHBORHOOD DEEP DIVE

### 16.1 Descrição

**Neighborhood Deep Dive** é a página com amenidades (escolas, metro, hospitais, comércio), safety scores, walkability, transit scores, future development plans e school ratings. Inspirado no Neighborhoods do Zillow e Area Insights do AirDNA.

**Objectivo:** Analisar a qualidade e potencial de cada freguesia.

### 16.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🗺️ NEIGHBORHOOD DEEP DIVE — Análise de Freguesias                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SELECT FREGUESIA: [Cedofeita ▼]                                            │
│                                                                             │
│  KPIs:                                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Walkability│Transit  │Safety   │Schools  │Amenities│              │
│  │   85/100 │   78/100 │   92/100 │   88/100 │   95/100 │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  MAPA COM POIs (escolas, metro, hospitais, comércio):                       │
│  [Mapa interativo com layers]                                               │
│                                                                             │
│  FUTURE DEVELOPMENT:                                                         │
│  - 2026: Nova linha metro Cedofeita                                        │
│  - 2027: Parque urbano Bonfim                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.3 Implementação

```python
st.header("🏘️ Neighborhood Deep Dive")

import plotly.express as px
import pandas as pd

# Neighborhood selector
neighborhood = st.selectbox("Selecionar Freguesia", ["Cedofeita", "Boavista", "Campanhã", "Bonfim", "Vitória", "Paranhos"])

# Scores overview
col1, col2, col3, col4, col5 = st.columns(5)
scores = {"Cedofeita": [8.5, 9.2, 7.8, 8.0, 9.5], "Boavista": [9.1, 8.5, 8.8, 7.5, 9.0],
          "Campanhã": [7.2, 6.8, 7.5, 8.5, 7.0], "Bonfim": [8.0, 8.8, 7.2, 7.8, 8.5],
          "Vitória": [9.0, 9.5, 8.5, 6.5, 9.2], "Paranhos": [7.5, 7.0, 8.0, 9.0, 7.8]}

s = scores.get(neighborhood, [7.0]*5)
with col1: st.metric("Walk Score", f"{s[0]}/10", "Mobilidade a pé")
with col2: st.metric("Transit Score", f"{s[1]}/10", "Transportes públicos")
with col3: st.metric("Safety", f"{s[2]}/10", "Segurança")
with col4: st.metric("Schools", f"{s[3]}/10", "Escolas")
with col5: st.metric("Amenities", f"{s[4]}/10", "Comércio/Serviços")

# Amenities radar chart
categories = ['Mobilidade', 'Transportes', 'Segurança', 'Escolas', 'Comércio', 'Lazer']
values = s + [8.0]  # Add leisure score

fig = px.line_polar(r=values, theta=categories, line_close=True)
fig.update_traces(fill='toself', line_color='blue')
fig.update_layout(title=f"Perfil de {neighborhood}", polar=dict(radialaxis=dict(visible=True, range=[0, 10])))
st.plotly_chart(fig, use_container_width=True)

# Amenities list
st.subheader("📍 Amenidades Próximas")
amenities = {
    "Cedofeita": [("Metro Trindade", "transport", "0.3km"), ("Hospital Santo António", "health", "0.8km"), 
                 ("Pingo Doce", "shop", "0.2km"), ("Escola Secundária", "school", "0.5km")],
    "Boavista": [("Metro Casa da Música", "transport", "0.2km"), ("Hospital Lusíadas", "health", "1.2km"),
                 ("Continente", "shop", "0.4km"), ("Colégio D. Diogo", "school", "0.6km")],
    "Campanhã": [("Estação Campanhã", "transport", "0.1km"), ("Hospital S. João", "health", "2.0km"),
                 ("Minipreço", "shop", "0.5km"), ("Escola Básica", "school", "0.8km")]
}

for amenity in amenities.get(neighborhood, []):
    name, icon, dist = amenity
    emoji = {"transport": "🚇", "health": "🏥", "shop": "🛒", "school": "🏫"}.get(icon, "📍")
    st.markdown(f"{emoji} **{name}** — {dist}")

# School ratings
st.subheader("🏫 School Ratings")
schools_data = [
    {"name": "Escola Secundária A", "rating": 8.5, "reviews": 120, "distance": "0.5km"},
    {"name": "Escola Básica B", "rating": 7.8, "reviews": 85, "distance": "0.8km"},
    {"name": "Colégio Privado C", "rating": 9.2, "reviews": 45, "distance": "1.2km"}
]

for school in schools_data:
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1: st.markdown(f"**{school['name']}**")
    with c2: st.markdown(f"⭐ {school['rating']}/10")
    with c3: st.caption(f"{school['distance']} | {school['reviews']} reviews")

# Future development plans
st.subheader("🏗️ Future Development Plans")
plans = [
    {"project": "Nova Linha Metro", "status": "Em construção", "impact": "Alta", "completion": "2025"},
    {"project": "Centro Comercial Novo", "status": "Aprovado", "impact": "Média", "completion": "2026"},
    {"project": "Parque Urbano", "status": "Planeado", "impact": "Média", "completion": "2027"}
]

for plan in plans:
    impact_color = "green" if plan['impact'] == "Alta" else "orange" if plan['impact'] == "Média" else "gray"
    st.markdown(f"- **{plan['project']}** | Status: `{plan['status']}` | Impacto: <span style='color:{impact_color}'>{plan['impact']}</span> | Conclusão: {plan['completion']}", unsafe_allow_html=True)

# Price trends by neighborhood
st.subheader("📈 Price Trends por Freguesia")
trends_data = pd.DataFrame({
    "Mês": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
    "Cedofeita": [2100, 2120, 2150, 2130, 2180, 2200],
    "Boavista": [2300, 2320, 2350, 2380, 2400, 2420],
    "Campanhã": [1800, 1820, 1850, 1840, 1860, 1880]
})

fig2 = px.line(trends_data, x="Mês", y=["Cedofeita", "Boavista", "Campanhã"], title="Evolução €/m² por Freguesia")
fig2.update_layout(xaxis_title="Mês", yaxis_title="€/m²")
st.plotly_chart(fig2, use_container_width=True)
```

---

## 17. PÁGINA: CONFIGURAÇÕES AVANÇADAS

### 17.1 Descrição

Página de configurações enterprise com múltiplas secções: notificações, thresholds, scraping, investment defaults, UI preferences, data management e system admin.

### 17.2 Layout

*Ver secção 16.2 do documento original para layout completo.*

### 17.3 Implementação

```python
import streamlit as st
from utils.config import ConfigManager

st.header("⚙️ Configurações Avançadas")

config = ConfigManager()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📱 Telegram", "🔔 Notificações", "💰 Investment", "🌐 Scraping", "🎨 UI"
])

with tab1:
    st.subheader("Telegram Bot Configuration")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        token = st.text_input("Bot Token", value=config.get("telegram.token", ""), type="password")
    with col2:
        if st.button("👁️", help="Mostrar token"):
            st.info(f"Token: {token[:10]}...")
    
    chat_ids = st.text_area("Chat IDs (um por linha)", value="\n".join(config.get("telegram.chat_ids", [])),
                           help="IDs dos chats para receber notificações")
    
    c1, c2 = st.columns(2)
    with c1:
        rate_limit = st.number_input("Rate Limit (notif/dia)", 1, 50, 
                                    config.get("telegram.rate_limit", 5))
    with c2:
        quiet_start = st.time_input("Quiet Hours Start", value=config.get("telegram.quiet_start", "23:00"))
        quiet_end = st.time_input("Quiet Hours End", value=config.get("telegram.quiet_end", "08:00"))
    
    if st.button("🧪 Send Test Notification", type="primary"):
        # Trigger test notification via backend
        st.success("Test notification sent!")
    
    st.divider()
    if st.button("💾 Save Telegram Config", use_container_width=True):
        config.set_multi({
            "telegram.token": token,
            "telegram.chat_ids": [x.strip() for x in chat_ids.split("\n") if x.strip()],
            "telegram.rate_limit": rate_limit,
            "telegram.quiet_start": str(quiet_start),
            "telegram.quiet_end": str(quiet_end)
        })
        st.toast("Telegram config saved!")

with tab2:
    st.subheader("Advanced Alert Rules")
    
    st.markdown("#### 🚨 Instant Alerts (push immediately)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.toggle("Imperdível Alert", value=config.get("alerts.imperdivel.enabled", True),
                 help="Score ≥ threshold")
        st.number_input("Threshold", 8.0, 10.0, config.get("alerts.imperdivel.threshold", 9.0), step=0.1)
    with col2:
        st.toggle("Price Drop Alert", value=config.get("alerts.price_drop.enabled", True))
        st.slider("Drop %", 5, 50, config.get("alerts.price_drop.threshold", 10))
    with col3:
        st.toggle("New Listing Alert", value=config.get("alerts.new_listing.enabled", True))
        st.number_input("Min Score", 0.0, 10.0, config.get("alerts.new_listing.score_min", 8.0), step=0.5)
        st.slider("Min Discount %", 0, 50, config.get("alerts.new_listing.discount_min", 15))
    
    st.markdown("#### 📊 Scheduled Digests")
    col1, col2 = st.columns(2)
    with col1:
        st.toggle("Daily Digest", value=config.get("digest.daily.enabled", True))
        st.time_input("Time", value=config.get("digest.daily.time", "08:00"))
        st.number_input("Top N", 3, 20, config.get("digest.daily.top_n", 5))
    with col2:
        st.toggle("Weekly Report", value=config.get("digest.weekly.enabled", True))
        st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    .index(config.get("digest.weekly.day", "Monday")))
    
    st.markdown("#### 🔍 Filter Scope")
    st.multiselect("Freguesias", ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória', 'Massarelos'],
                  default=config.get("alerts.freguesias", ['Cedofeita', 'Paranhos', 'Bonfim']))
    st.slider("Price Range (€)", 0, 1000000,
             (config.get("alerts.price_min", 50000), config.get("alerts.price_max", 500000)),
             step=10000)
    st.multiselect("Tipologia", ['T0', 'T1', 'T2', 'T3', 'T4', 'T5+'],
                  default=config.get("alerts.tipos", ['T2', 'T3', 'T4']))
    
    if st.button("💾 Save Alert Config", use_container_width=True):
        st.toast("Alert config saved!")

with tab3:
    st.subheader("Investment Default Parameters")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Down Payment %", 0, 100, config.get("investment.down_payment", 20))
        st.number_input("Interest Rate %", 0.0, 20.0, config.get("investment.interest_rate", 3.5), step=0.1)
        st.number_input("Loan Term (years)", 5, 50, config.get("investment.loan_term", 30))
    with col2:
        st.number_input("Monthly Expenses (€)", 0, 2000, config.get("investment.monthly_expenses", 200))
        st.number_input("Est. Rental Yield %", 0.0, 20.0, config.get("investment.rental_yield", 5.5), step=0.1)
        st.selectbox("Tax Bracket", ["IRS 14%", "IRS 23%", "IRS 28%", "IRS 35%", "IRS 37%", "IRS 45%", "IRS 48%"],
                    index=["IRS 14%", "IRS 23%", "IRS 28%", "IRS 35%", "IRS 37%", "IRS 45%", "IRS 48%"]
                    .index(config.get("investment.tax_bracket", "IRS 28%")))
    with col3:
        st.number_input("Target Cap Rate %", 0.0, 20.0, config.get("investment.target_cap_rate", 6.0), step=0.1)
        st.number_input("Target Cash-on-Cash %", 0.0, 30.0, config.get("investment.target_coc", 8.0), step=0.1)
        st.number_input("Target IRR %", 0.0, 30.0, config.get("investment.target_irr", 12.0), step=0.1)
    
    if st.button("💾 Save Investment Config", use_container_width=True):
        st.toast("Investment defaults saved!")

with tab4:
    st.subheader("Scraping Engine Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.select_slider("Frequency", options=["15 min", "30 min", "1 hour", "2 hours", "4 hours", "8 hours", "Manual"],
                        value=config.get("scraping.frequency", "30 min"))
        st.multiselect("Active Portals", 
                      ['Idealista', 'Imovirtual', 'Casa Sapo', 'OLX', 'ERA', 'Century21', 'SuperCasa', 'REMAX'],
                      default=config.get("scraping.portals", ['Idealista', 'Imovirtual', 'Casa Sapo', 'OLX']))
        st.slider("Concurrent Browsers", 1, 5, config.get("scraping.concurrent_browsers", 3))
    with col2:
        st.selectbox("Proxy Mode", ["Auto Rotate", "Fixed", "None"], 
                    index=["Auto Rotate", "Fixed", "None"].index(config.get("scraping.proxy_mode", "Auto Rotate")))
        st.slider("Request Delay (s)", 1.0, 10.0, 
                 (config.get("scraping.delay_min", 2.0), config.get("scraping.delay_max", 5.0)), step=0.5)
        st.number_input("Max Pages per Portal", 1, 50, config.get("scraping.max_pages", 10))
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Force Scrape Now", type="primary", use_container_width=True):
            st.warning("Scrape triggered! Check System page for progress.")
    with col2:
        if st.button("📊 View Scraping Logs", use_container_width=True):
            st.switch_page("pages/11_system.py")
    
    if st.button("💾 Save Scraping Config", use_container_width=True):
        st.toast("Scraping config saved!")

with tab5:
    st.subheader("UI Preferences")
    
    col1, col2 = st.columns(2)
    with col1:
        theme = st.segmented_control("Theme", ["☀️ Light", "🌙 Dark", "💻 System"],
                                     default=config.get("ui.theme", "☀️ Light"))
        lang = st.selectbox("Language", ["Português", "English", "Español"],
                           index=["Português", "English", "Español"].index(config.get("ui.language", "Português")))
        currency = st.selectbox("Currency", ["EUR €", "USD $", "GBP £"],
                               index=["EUR €", "USD $", "GBP £"].index(config.get("ui.currency", "EUR €")))
    with col2:
        number_fmt = st.selectbox("Number Format", ["1.234,56", "1,234.56", "1 234,56"],
                                 index=["1.234,56", "1,234.56", "1 234,56"].index(config.get("ui.number_format", "1.234,56")))
        st.toggle("Auto-refresh", value=config.get("ui.auto_refresh", True))
        st.number_input("Refresh Interval (min)", 1, 60, config.get("ui.refresh_interval", 5))
        st.selectbox("Default Map Style", ["CartoDB Positron", "OpenStreetMap", "Satellite"],
                    index=["CartoDB Positron", "OpenStreetMap", "Satellite"]
                    .index(config.get("ui.map_style", "CartoDB Positron")))
        st.selectbox("Table Page Size", [25, 50, 100, 200], 
                    index=[25, 50, 100, 200].index(config.get("ui.page_size", 50)))
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Preferences", type="primary", use_container_width=True):
            st.toast("Preferences saved!")
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.warning("Reset to defaults?")
```

---

## 10. PÁGINA: MARKET INTELLIGENCE

### 10.1 Descrição

**Market Intelligence** é a página de análise avançada de mercado com dados INE, forecasting de preços, seasonality analysis, detecção de tendências (bull/bear signals) e comparação entre freguesias. Inspirado em Zillow Research, Idealista Trends e AirDNA Market Intelligence.

### 10.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 MARKET INTELLIGENCE — Porto, Portugal                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: MARKET KPIs                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Preço/m² │ │Δ Anual  │ │Listings │ │Velocity │ │Sentiment│              │
│  │ €2,850  │ │ +8.4% ▲│ │ 4,891  │ │ 45 dias│ │ Bullish │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  ROW 2: TABS — [Price Trends] [Forecasting] [Seasonality] [Compare Zones] │
│                                                                             │
│  TAB: PRICE TRENDS                                                         │
│  ┌────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Price/m² por Freguesia (Line)  │  │ Price Heatmap (Freg × Typology)│  │
│  │ 2022 → 2023 → 2024 → 2025     │  │ T1│T2│T3│T4│T5               │  │
│  │                                │  │ Ced│2.9│2.6│2.3│2.0│1.7      │  │
│  │                                │  │ Par│2.8│2.5│2.2│1.9│1.6      │  │
│  │                                │  │ ...                             │  │
│  └────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  TAB: FORECASTING (XGBoost 6-12 meses)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Actual: ~~~~~~~ ~~~~~~~~                                          │  │
│  │ Forecast: ─ ─ ─ ─ ─ ─ (dashed line with confidence interval)       │  │
│  │ Confidence: [====] 80% CI                                        │  │
│  │                                     │  Bullish/Bearish indicator    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TAB: SEASONALITY                                                         │
│  ┌────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Monthly Price Pattern (Radar)   │  │ Best Buy/Sell Months          │  │
│  │ Jan Feb Mar Apr May Jun Jul...  │  │ 🟢 Buy: Jan-Feb, Sep-Oct       │  │
│  │                                 │  │ 🔴 Sell: Apr-May, Jun-Jul      │  │
│  └────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Implementação

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.header("📊 Market Intelligence")
st.caption("Análise de mercado com dados INE e forecasting ML — Porto, Portugal")

# KPIs
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Preço/m² Médio", "€2,850", "+8.4%", delta_color="normal")
kpi2.metric("Listings Activos", "4,891", "+98", delta_color="normal")
kpi3.metric("Market Velocity", "45 dias", "-3 dias", delta_color="inverse")
kpi4.metric("Sentimento", "🐂 Bullish", "↗️ Strong", delta_color="off")
kpi5.metric("Forecast 6M", "+5.2%", "±2.1%", delta_color="off")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Trends", "🔮 Forecasting", "📅 Seasonality", "⚖️ Compare Zones"])

with tab1:
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        st.subheader("Evolução Preço/m² por Freguesia")
        timeline = pd.DataFrame({
            'trimestre': ['2022-Q1', '2022-Q2', '2022-Q3', '2022-Q4', '2023-Q1', '2023-Q2', 
                         '2023-Q3', '2023-Q4', '2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4',
                         '2025-Q1', '2025-Q2', '2025-Q3', '2025-Q4'],
            'Cedofeita': [2400, 2450, 2500, 2550, 2600, 2650, 2700, 2750, 2800, 2850, 2900, 2950,
                         3000, 3050, 3100, 3150],
            'Paranhos': [2300, 2350, 2400, 2420, 2450, 2500, 2550, 2600, 2650, 2700, 2750, 2800,
                        2850, 2900, 2950, 3000],
            'Bonfim': [2200, 2250, 2300, 2350, 2400, 2420, 2450, 2500, 2550, 2600, 2650, 2700,
                      2750, 2800, 2850, 2900],
            'Baixa': [2600, 2650, 2700, 2750, 2800, 2850, 2900, 2950, 3000, 3050, 3100, 3150,
                     3200, 3250, 3300, 3350]
        })
        fig = px.line(timeline.melt(id_vars='trimestre', var_name='Freguesia', value_name='Preço/m²'),
                     x='trimestre', y='Preço/m²', color='Freguesia',
                     title="Preço/m² por Trimestre — INE Data",
                     markers=True)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Heatmap Preço/m² × Tipologia")
        heatmap_data = pd.DataFrame({
            'freguesia': ['Baixa', 'Vitória', 'Cedofeita', 'Bonfim', 'Paranhos', 'Massarelos'],
            'T1': [3200, 3000, 2800, 2700, 2600, 2500],
            'T2': [2900, 2750, 2600, 2500, 2400, 2300],
            'T3': [2600, 2500, 2350, 2250, 2200, 2100],
            'T4': [2300, 2200, 2100, 2000, 1950, 1850],
            'T5+': [2000, 1900, 1800, 1750, 1700, 1600]
        }).set_index('freguesia')
        fig = px.imshow(heatmap_data, text_auto=True, aspect='auto',
                       color_continuous_scale='RdYlGn_r',
                       title="€/m² por Freguesia e Tipologia")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🔮 Price Forecasting (XGBoost — 6 meses)")
    
    forecast_df = pd.DataFrame({
        'month': pd.date_range(start='2026-01', periods=12, freq='MS'),
        'actual': [3150, 3180, 3200, 3220, 3250, 3280, None, None, None, None, None, None],
        'forecast': [None, None, None, None, None, 3280, 3310, 3340, 3380, 3420, 3450, 3480],
        'ci_lower': [None, None, None, None, None, 3250, 3270, 3290, 3320, 3360, 3380, 3400],
        'ci_upper': [None, None, None, None, None, 3310, 3350, 3390, 3440, 3480, 3520, 3560]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast_df['month'], y=forecast_df['actual'],
                            mode='lines+markers', name='Actual', line=dict(color='#1E88E5')))
    fig.add_trace(go.Scatter(x=forecast_df['month'], y=forecast_df['forecast'],
                            mode='lines+markers', name='Forecast', line=dict(color='#43A047', dash='dash')))
    fig.add_trace(go.Scatter(x=forecast_df['month'].tolist() + forecast_df['month'].tolist()[::-1],
                            y=forecast_df['ci_upper'].tolist() + forecast_df['ci_lower'].tolist()[::-1],
                            fill='toself', fillcolor='rgba(67,160,71,0.2)',
                            line=dict(color='rgba(0,0,0,0)'), name='80% CI'))
    fig.update_layout(title="Preço/m² Forecast — Cedofeita", yaxis_title="€/m²")
    st.plotly_chart(fig, use_container_width=True)
    
    bull_cols = st.columns(3)
    bull_cols[0].metric("Forecast 6M", "+5.2%", "📈 Bullish")
    bull_cols[1].metric("Confidence", "82%", "Good")
    bull_cols[2].metric("Best Entry", "Mar-Apr 2026", "📅 Seasonal low")

with tab3:
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        st.subheader("Seasonality Pattern (5-year average)")
        seasonality = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'price_index': [96, 95, 97, 100, 102, 103, 102, 101, 99, 98, 97, 96],
            'volume_index': [85, 88, 95, 105, 110, 108, 102, 98, 95, 92, 88, 82]
        })
        fig = px.line(seasonality.melt(id_vars='month', var_name='Metric', value_name='Index'),
                     x='month', y='Index', color='Metric', markers=True,
                     title="Índice Sazonal — Preço vs Volume")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("📅 Best Timing")
        st.success("🟢 **Melhor época para comprar:**\nJaneiro-Fevereiro, Setembro-Outubro\n(Preços 3-5% abaixo da média)")
        st.error("🔴 **Melhor época para vender:**\nAbril-Maio, Junho-Julho\n(Preços 2-3% acima da média)")
        st.info("📊 **Volume alto:** Maio-Junho\n📊 **Volume baixo:** Dezembro-Janeiro")

with tab4:
    st.subheader("⚖️ Comparative Zone Analysis")
    compare_df = pd.DataFrame({
        'Freguesia': ['Cedofeita', 'Paranhos', 'Bonfim', 'Baixa', 'Vitória', 'Massarelos'],
        'Preço/m²': [3150, 3000, 2900, 3350, 3200, 2800],
        'Crescimento 1A': ['+8.4%', '+7.2%', '+6.8%', '+9.1%', '+8.0%', '+5.5%'],
        'Crescimento 3A': ['+28%', '+24%', '+22%', '+32%', '+29%', '+18%'],
        'Velocity (dias)': [42, 48, 52, 38, 45, 55],
        'Score Médio': [6.8, 6.2, 5.9, 7.2, 6.5, 5.5]
    })
    st.dataframe(compare_df, use_container_width=True, hide_index=True)
    
    fig = px.scatter(compare_df, x='Preço/m²', y='Score Médio',
                      size='Velocity (dias)', color='Crescimento 1A',
                      hover_name='Freguesia',
                      title="Zone Matrix: Preço vs Score (tamanho = velocidade)")
    st.plotly_chart(fig, use_container_width=True)
```

---

## 18. PÁGINA: TELEGRAM & NOTIFICAÇÕES

### 17.1 Descrição

Página de gestão de notificações Telegram com histórico completo, estatísticas de delivery, reenvio de notificações falhadas, e preview de mensagens formatadas.

### 17.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📱 TELEGRAM & NOTIFICAÇÕES                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: NOTIFICATION KPIs                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ Total   │ │Sucesso  │ │Falhadas │ │Rate     │ │Última   │              │
│  │ 1,247   │ │ 98.4%   │ │ 20      │ │ 5/dia   │ │ 14:30   │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  TABS: [History] [Stats] [Preview] [Failed] [Test]                        │
│                                                                             │
│  TAB: HISTORY — Tabela com todas as notificações enviadas                  │
│  TAB: STATS — Gráficos de envio por dia, por tipo, por sucesso            │
│  TAB: PREVIEW — Preview de como a mensagem aparece no Telegram           │
│  TAB: FAILED — Lista de falhas com retry                                 │
│  TAB: TEST — Enviar notificação de teste manualmente                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 Implementação

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.header("📱 Telegram & Notificações")

# KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Enviadas", "1,247", "+12 hoje")
k2.metric("Taxa Sucesso", "98.4%", "+0.2%")
k3.metric("Falhadas", "20", "-2", delta_color="inverse")
k4.metric("Rate Médio", "5.2/dia", "↔️")
k5.metric("Última", "14:32", "há 18 min")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📜 History", "📊 Stats", "👁️ Preview", "❌ Failed", "🧪 Test"])

with tab1:
    @st.cache_data(ttl=60)
    def get_notification_history():
        return pd.DataFrame({
            'timestamp': pd.date_range(end=datetime.now(), periods=50, freq='30min'),
            'tipo': ['Imperdível']*15 + ['Price Drop']*10 + ['New Listing']*15 + ['Daily Digest']*10,
            'titulo': ['T3 Cedofeita €180k']*50,
            'score': [9.2]*15 + [8.5]*10 + [8.1]*15 + [None]*10,
            'discount': [25.0]*15 + [18.0]*10 + [15.0]*15 + [None]*10,
            'chat_id': ['123456789']*50,
            'status': ['✅ Enviado']*49 + ['❌ Falhou'],
            'error': [None]*49 + ['Timeout']
        })
    
    hist = get_notification_history()
    
    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        tipo_filter = st.multiselect("Tipo", hist['tipo'].unique(), default=hist['tipo'].unique())
    with f2:
        status_filter = st.multiselect("Status", hist['status'].unique(), default=hist['status'].unique())
    with f3:
        date_range = st.date_input("Período", [datetime.now()-timedelta(days=7), datetime.now()])
    
    filtered = hist[hist['tipo'].isin(tipo_filter) & hist['status'].isin(status_filter)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        daily = hist.groupby(hist['timestamp'].dt.date).size().reset_index(name='count')
        fig = px.bar(daily, x='timestamp', y='count', title="Notificações por Dia")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        by_type = hist.groupby('tipo').size().reset_index(name='count')
        fig = px.pie(by_type, values='count', names='tipo', title="Por Tipo de Alerta")
        st.plotly_chart(fig, use_container_width=True)
    
    success_rate = hist.groupby(hist['timestamp'].dt.date).apply(
        lambda x: (x['status'] == '✅ Enviado').mean() * 100
    ).reset_index(name='success_rate')
    fig = px.line(success_rate, x='timestamp', y='success_rate',
                 title="Taxa de Sucesso ao Longo do Tempo (%)", markers=True)
    fig.update_layout(yaxis_range=[90, 100])
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Preview da Mensagem Telegram")
    st.markdown("""
    ---
    🏠 **NOVA OPORTUNIDADE — Score: 9.2/10 ⭐**
    
    **T3 Renovado em Cedofeita**
    💰 Preço: €180,000 (Discount: 25%)
    📏 Área: 85m² | 🛏️ 3 Quartos
    🎯 Valor Justo: €240,000
    
    📍 Cedofeita, Porto
    ⏰ Anúncio publicado há 2 dias
    🔗 [Ver no Idealista](https://...)
    
    💡 **Rationale:** Preço 25% abaixo do valor justo. Zona premium com metro a 5 min. Imóvel renovado em 2023.
    ---
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Message Format Options:**")
        st.toggle("Include Photos", value=True)
        st.toggle("Include Map Link", value=True)
        st.toggle("Include Comps", value=False)
    with col2:
        st.markdown("**Style:**")
        st.select_slider("Detail Level", ["Minimal", "Standard", "Verbose"], value="Standard")

with tab4:
    failed = hist[hist['status'] == '❌ Falhou']
    if len(failed) > 0:
        st.error(f"{len(failed)} notificações falhadas")
        st.dataframe(failed[['timestamp', 'tipo', 'titulo', 'error']], use_container_width=True)
        if st.button("🔄 Retry All Failed", type="primary"):
            st.success("Retrying failed notifications...")
    else:
        st.success("🎉 Nenhuma notificação falhada!")

with tab5:
    st.subheader("Enviar Notificação de Teste")
    test_chat = st.text_input("Chat ID", value="123456789")
    test_msg = st.text_area("Mensagem de Teste", value="🧪 Teste do Real Estate Opportunity Engine!")
    if st.button("📤 Enviar Teste", type="primary"):
        st.success(f"Teste enviado para {test_chat}!")
```

---

## 18. PÁGINA: SYSTEM & DEVOPS

### 18.1 Descrição

**System & DevOps** é a página de monitorização do sistema com health checks em tempo real, logs estruturados com filtering, métricas de performance por componente, e ferramentas de diagnóstico (database status, disk usage, memory).

### 18.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🖥️ SYSTEM & DEVOPS — Monitorização e Diagnóstico                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROW 1: SYSTEM HEALTH CARDS                                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Scraping │ │ETL      │ │Valuation│ │Scoring  │ │Notif.   │              │
│  │ ✅ OK   │ │ ✅ OK   │ │ ✅ OK   │ │ ✅ OK   │ │ ✅ OK   │              │
│  │Last:2m  │ │Last:5m  │ │Last:7m  │ │Last:9m  │ │Last:12m │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  ROW 2: RESOURCE USAGE                                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                                      │
│  │CPU: 23% │ │RAM: 45% │ │Disk: 67%│                                      │
│  │ ▓▓▓░░   │ │ ▓▓▓▓░   │ │ ▓▓▓▓▓▓░ │                                      │
│  └─────────┘ └─────────┘ └─────────┘                                      │
│                                                                             │
│  TABS: [Logs] [Performance] [Database] [Network] [Diagnostics]            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.3 Implementação

```python
import streamlit as st
import pandas as pd
from datetime import datetime

st.header("🖥️ System & DevOps")
st.caption(f"Status em tempo real | Uptime: 14d 3h 22m | v2.1.0")

# Health Cards
health = {
    'Scraping': {'status': '✅ OK', 'last': '2 min ago', 'color': 'green'},
    'ETL Pipeline': {'status': '✅ OK', 'last': '5 min ago', 'color': 'green'},
    'Valuation Engine': {'status': '✅ OK', 'last': '7 min ago', 'color': 'green'},
    'Scoring Engine': {'status': '✅ OK', 'last': '9 min ago', 'color': 'green'},
    'Notifications': {'status': '✅ OK', 'last': '12 min ago', 'color': 'green'},
    'Database': {'status': '✅ OK', 'last': '1 min ago', 'color': 'green'},
    'Dashboard': {'status': '✅ OK', 'last': 'Active', 'color': 'green'}
}

hcols = st.columns(7)
for col, (name, info) in zip(hcols, health.items()):
    with col:
        st.metric(name, info['status'], info['last'], delta_color="off")

st.divider()

# Resource Usage
r1, r2, r3 = st.columns(3)
r1.metric("CPU Usage", "23%", "▓▓▓░░░░░░░")
r2.metric("RAM Usage", "45%", "▓▓▓▓▓░░░░░")
r3.metric("Disk Usage", "67%", "▓▓▓▓▓▓▓░░░")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📜 Logs", "📊 Performance", "🗄️ Database", "🌐 Network", "🔧 Diagnostics"])

with tab1:
    log_filter = st.multiselect("Level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                               default=["INFO", "WARNING", "ERROR"])
    component_filter = st.multiselect("Component", ["Scraping", "ETL", "Valuation", "Scoring", "Notification", "Dashboard"],
                                     default=["Scraping", "ETL", "Valuation", "Scoring", "Notification"])
    search = st.text_input("Search logs")
    
    logs_df = pd.DataFrame({
        'timestamp': pd.date_range(end=datetime.now(), periods=100, freq='1min'),
        'level': ['INFO']*80 + ['WARNING']*12 + ['ERROR']*8,
        'component': ['Scraping']*30 + ['ETL']*25 + ['Valuation']*20 + ['Scoring']*15 + ['Notification']*10,
        'message': ['Scraped 45 listings from Idealista']*30 + ['Normalized 42 listings']*25 + 
                  ['Valuated 40 listings']*20 + ['Scored 38 listings']*15 + ['Sent 3 notifications']*10
    })
    
    filtered_logs = logs_df[logs_df['level'].isin(log_filter) & logs_df['component'].isin(component_filter)]
    if search:
        filtered_logs = filtered_logs[filtered_logs['message'].str.contains(search, case=False, na=False)]
    
    st.dataframe(filtered_logs, use_container_width=True, hide_index=True)

with tab2:
    perf_df = pd.DataFrame({
        'component': ['Scraping', 'ETL', 'Valuation', 'Scoring', 'Notification', 'Dashboard'],
        'avg_time_s': [720, 180, 300, 120, 30, 2],
        'max_time_s': [1200, 360, 600, 240, 60, 5],
        'min_time_s': [300, 90, 150, 60, 10, 1],
        'throughput_per_hour': [200, 800, 500, 1000, 200, 5000]
    })
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(perf_df, x='component', y='avg_time_s',
                    title="Tempo Médio de Execução (segundos)", color='component')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(perf_df, x='component', y='throughput_per_hour',
                    title="Throughput (items/hora)", color='component')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Database Status")
    db_stats = pd.DataFrame({
        'Table': ['raw_listings', 'clean_listings', 'valuations', 'scores', 'notifications', 'price_history'],
        'Rows': [15234, 14890, 14100, 14100, 1247, 3650],
        'Size_MB': [45.2, 38.5, 22.1, 18.3, 5.2, 12.8],
        'Last_Write': ['2 min ago', '5 min ago', '7 min ago', '9 min ago', '12 min ago', '1 day ago'],
        'Index_Size_MB': [12.3, 10.5, 8.2, 6.1, 2.0, 4.5]
    })
    st.dataframe(db_stats, use_container_width=True, hide_index=True)
    
    if st.button("🗜️ Run VACUUM", use_container_width=True):
        st.success("Database optimized!")
    if st.button("📤 Export Full Backup", use_container_width=True):
        st.info("Backup started — check logs")

with tab4:
    st.subheader("Network & Scraping Status")
    net_df = pd.DataFrame({
        'Portal': ['Idealista', 'Imovirtual', 'Casa Sapo', 'OLX', 'ERA', 'Century21', 'SuperCasa', 'REMAX'],
        'Status': ['✅ Active']*8,
        'Last_Scrape': ['2m', '8m', '15m', '22m', '45m', '45m', '1h', '1h'],
        'Success_Rate': [94.2, 91.5, 88.3, 85.0, 92.1, 90.5, 87.2, 89.8],
        'Avg_Delay_s': [3.2, 4.1, 5.5, 6.2, 3.8, 4.5, 5.8, 4.9],
        'Listings_Last': [45, 32, 28, 15, 12, 10, 8, 11]
    })
    st.dataframe(net_df, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("System Diagnostics")
    
    diag1, diag2 = st.columns(2)
    with diag1:
        st.markdown("#### Database Integrity")
        if st.button("🔍 Check DB Integrity", use_container_width=True):
            st.success("✅ All tables OK | 0 orphaned records | 0 duplicates")
        
        st.markdown("#### Cache Status")
        if st.button("🧹 Clear All Caches", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Caches cleared!")
    with diag2:
        st.markdown("#### Log Management")
        st.slider("Log Retention (days)", 7, 90, 30)
        if st.button("🗑️ Rotate Logs", use_container_width=True):
            st.success("Logs rotated!")
        
        st.markdown("#### System")
        if st.button("🔄 Restart Scheduler", use_container_width=True):
            st.warning("Scheduler restart triggered!")
```

---

## 20. PÁGINA: DATA QUALITY & DIAGNOSTICS

### 20.1 Descrição

**Data Quality & Diagnostics** é a página com data quality score, missing data analysis, duplicate detection, outlier visualization, data lineage e repair tools. Inspirado no Great Expectations e DataDog.

**Objectivo:** Monitorizar e garantir a qualidade dos dados do sistema.

### 20.2 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔍 DATA QUALITY & DIAGNOSTICS — Monitorização de Dados                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OVERALL QUALITY SCORE:                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Raw Data │Clean Data│Valuation│Scoring  │Overall  │              │
│  │  92%    │  95%     │  98%     │  97%     │  96%     │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  TABS: [Missing Data] [Duplicates] [Outliers] [Lineage] [Repair Tools]      │
│                                                                             │
│  TAB: MISSING DATA                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Campo                │ Missing % │ Impact    │ Action                  │   │
│  │ certificado_energético│  15%      │ Medium    │ [Fill] [Ignore]       │   │
│  │ descricao            │   2%      │ Low       │ [Fill] [Ignore]       │   │
│  │ ano_construcao        │   8%      │ High      │ [Fill] [Ignore]       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 20.3 Implementação

```python
st.header("🔍 Data Quality & Diagnostics")

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Overall quality scores
st.subheader("📊 Overall Quality Score")
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("Raw Data", "92%", "Scraping")
with col2: st.metric("Clean Data", "95%", "ETL")
with col3: st.metric("Valuation", "98%", "Pricing")
with col4: st.metric("Scoring", "97%", "ML")
with col5: st.metric("Overall", "96%", "Total")

st.progress(0.96)
st.markdown("**Data Quality Score: 96/100** — Excelente qualidade de dados")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📭 Missing Data", "🔄 Duplicates", "⚡ Outliers", "🧬 Lineage", "🔧 Repair Tools"])

with tab1:
    st.subheader("Missing Data Analysis")
    missing_data = [
        {"campo": "certificado_energetico", "missing_pct": 15, "impact": "Medium", "records": 450},
        {"campo": "descricao", "missing_pct": 2, "impact": "Low", "records": 60},
        {"campo": "ano_construcao", "missing_pct": 8, "impact": "High", "records": 240},
        {"campo": "area_util", "missing_pct": 5, "impact": "High", "records": 150},
        {"campo": "preco_m2", "missing_pct": 3, "impact": "Medium", "records": 90},
        {"campo": "tipologia", "missing_pct": 1, "impact": "Low", "records": 30}
    ]
    
    df_missing = pd.DataFrame(missing_data)
    fig = go.Figure()
    colors = ["red" if i == "High" else "orange" if i == "Medium" else "green" for i in df_missing["impact"]]
    fig.add_trace(go.Bar(x=df_missing["campo"], y=df_missing["missing_pct"], marker_color=colors, name="Missing %"))
    fig.update_layout(title="Missing Data by Field", xaxis_title="Campo", yaxis_title="Missing %")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df_missing.style.highlight_max(subset=["missing_pct"], color="lightcoral"))
    
    for row in missing_data:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: st.markdown(f"**{row['campo']}** — {row['missing_pct']}% missing ({row['records']} records)")
        with c2: st.button(f"Fill", key=f"fill_{row['campo']}")
        with c3: st.button(f"Ignore", key=f"ignore_{row['campo']}")

with tab2:
    st.subheader("Duplicate Detection")
    st.warning("47 potential duplicates detected")
    
    duplicates = [
        {"id": 1, "listing_a": "T3 Cedofeita #1234", "listing_b": "T3 Cedofeita #1235", "similarity": 98, "action": "Merge"},
        {"id": 2, "listing_a": "T2 Boavista #5678", "listing_b": "T2 Boavista #5679", "similarity": 95, "action": "Review"},
        {"id": 3, "listing_a": "T4 Campanhã #9012", "listing_b": "T4 Campanhã #9013", "similarity": 92, "action": "Merge"}
    ]
    
    for dup in duplicates:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: st.markdown(f"**{dup['listing_a']}** ↔ **{dup['listing_b']}** — Similarity: {dup['similarity']}%")
        with c2: st.markdown(f"`{dup['action']}`")
        with c3: st.button("Review", key=f"review_dup_{dup['id']}")
    
    if st.button("Auto-merge High Confidence (>95%)"):
        st.success("23 duplicates auto-merged successfully!")

with tab3:
    st.subheader("Outlier Detection")
    
    outliers = [
        {"listing": "T1 Centro", "preco": 850000, "media_zona": 180000, "desvio": 372, "campo": "preco"},
        {"listing": "T5 Boavista", "preco": 120000, "media_zona": 350000, "desvio": -66, "campo": "preco"},
        {"listing": "T2 Cedofeita", "area_util": 350, "media_zona": 85, "desvio": 311, "campo": "area"}
    ]
    
    for out in outliers:
        st.markdown(f"⚠️ **{out['listing']}** — {out['campo']}: €{out['preco']:,} (média zona: €{out['media_zona']:,}, desvio: {out['desvio']}%)")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3, 4, 5], y=[180000, 195000, 210000, 850000, 175000], mode='markers', marker=dict(size=[10, 10, 10, 25, 10], color=['blue', 'blue', 'blue', 'red', 'blue']), name='Preços'))
    fig.update_layout(title="Price Outliers", xaxis_title="Index", yaxis_title="Preço (€)")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Data Lineage")
    st.markdown("```\nScraping → Raw DB → ETL → Clean DB → Valuation → Scoring → Dashboard\n```")
    st.markdown("- **Scraping**: 3,000 records collected (2024-01-15)")
    st.markdown("- **Raw DB**: 3,000 records stored")
    st.markdown("- **ETL**: 2,940 records processed (60 filtered out)")
    st.markdown("- **Clean DB**: 2,940 records stored")
    st.markdown("- **Valuation**: 2,880 records priced (60 missing data)")
    st.markdown("- **Scoring**: 2,850 records scored")
    st.markdown("- **Dashboard**: 2,850 records displayed")

with tab5:
    st.subheader("🔧 Repair Tools")
    
    repair_col1, repair_col2 = st.columns(2)
    with repair_col1:
        st.markdown("**Auto-fill Missing Data**")
        st.selectbox("Campo", ["certificado_energetico", "ano_construcao", "area_util", "preco_m2"])
        st.selectbox("Método", ["Média Zona", "Mediana", "Regressão", "Forward Fill", "Manual"])
        if st.button("Apply Auto-fill"):
            st.success("Missing data filled successfully!")
    
    with repair_col2:
        st.markdown("**Data Validation**")
        st.checkbox("Validar preços > €50k")
        st.checkbox("Validar area_util > 10m²")
        st.checkbox("Validar ano_construcao > 1800")
        if st.button("Run Validation"):
            st.success("Validation completed! 12 issues found.")
    
    st.markdown("**Export Report**")
    if st.button("Generate Quality Report"):
        st.download_button("Download PDF", b"Quality Report", "data_quality_report.pdf")
```

---

## 21. COMPONENTES UI AVANÇADOS

### 21.1 Reusable Components (Python Modules)

```python
# components/kpi_card.py
import streamlit as st
from typing import Optional

def render_kpi_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    icon: Optional[str] = None
):
    """Render KPI card com icon e sparkline option."""
    icon_str = f"{icon} " if icon else ""
    st.metric(
        label=f"{icon_str}{label}",
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )

# components/score_badge.py
import streamlit as st

def render_score_badge(score: float):
    """Render score badge com cor apropriada."""
    if score >= 9.0:
        color, emoji = "#8E24AA", "💎"
    elif score >= 8.0:
        color, emoji = "#43A047", "⭐"
    elif score >= 7.0:
        color, emoji = "#66BB6A", "✓"
    elif score >= 6.0:
        color, emoji = "#FB8C00", "~"
    else:
        color, emoji = "#E53935", "✗"
    
    st.markdown(
        f"<span style='background-color:{color};color:white;padding:4px 8px;"
        f"border-radius:12px;font-weight:bold;font-size:14px;'>{emoji} {score:.1f}</span>",
        unsafe_allow_html=True
    )

# components/listing_card.py
import streamlit as st
from dialogs.listing_detail import show_listing_detail

def render_listing_card(listing: dict, compact: bool = False):
    """Render listing card (compact ou expanded)."""
    with st.container(border=True):
        if compact:
            c1, c2, c3 = st.columns([0.5, 0.3, 0.2])
            with c1:
                st.markdown(f"**{listing['titulo']}**")
                st.caption(f"€{listing['preco']:,.0f} | {listing['area']}m² | {listing['freguesia']}")
            with c2:
                st.markdown(f"**{listing.get('discount', 0):.1f}%** discount")
            with c3:
                from components.score_badge import render_score_badge
                render_score_badge(listing['score'])
                if st.button("👁️", key=f"view_{listing['id']}"):
                    show_listing_detail(listing['id'])
        else:
            # Expanded view com fotos, descrição, mapa mini, etc.
            pass

# components/filter_panel.py
import streamlit as st
from typing import Dict, Any

def render_filter_panel(
    defaults: Dict[str, Any],
    on_apply: callable = None
) -> Dict[str, Any]:
    """Render reusable filter panel com saved searches."""
    with st.expander("🔍 Filtros", expanded=True):
        filters = {}
        col1, col2, col3 = st.columns(3)
        with col1:
            filters['preco_range'] = st.slider("Preço (€)", 0, 1000000,
                (defaults.get('preco_min', 50000), defaults.get('preco_max', 500000)), step=10000)
        with col2:
            filters['area_range'] = st.slider("Área (m²)", 0, 500,
                (defaults.get('area_min', 50), defaults.get('area_max', 200)), step=5)
        with col3:
            filters['score_min'] = st.slider("Score mínimo", 0.0, 10.0,
                defaults.get('score_min', 5.0), step=0.5)
        
        if on_apply and st.button("🔄 Aplicar", use_container_width=True):
            on_apply(filters)
    return filters
```

### 20.2 Dialog Components (st.dialog — Streamlit 1.42+)

```python
# dialogs/listing_detail.py
import streamlit as st

def show_listing_detail(listing_id: str):
    """Show rich listing detail modal."""
    @st.dialog("📄 Listing Detail", width="large")
    def detail_modal():
        # Fetch listing data
        listing = {"id": listing_id, "titulo": "T3 Cedofeita", "preco": 180000,
                  "valor_justo": 240000, "score": 9.2, "discount": 25.0}
        
        st.header(listing['titulo'])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Preço", f"€{listing['preco']:,.0f}")
        col2.metric("Valor Justo", f"€{listing['valor_justo']:,.0f}")
        col3.metric("Score", f"{listing['score']:.1f}")
        col4.metric("Discount", f"{listing['discount']:.1f}%")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Info", "📊 Valuation", "🗺️ Map", "📈 History"])
        
        with tab1:
            st.markdown("**Descrição completa do imóvel...**")
            st.link_button("🔗 Ver no Portal", "https://idealista.pt/...")
        with tab2:
            st.markdown("**Valuation breakdown:** Hedonic €230k | Comps €245k | INE €235k | XGB €242k")
        with tab3:
            st.map(data={"lat": [41.15], "lon": [-8.61]}, zoom=15)
        with tab4:
            st.line_chart({"price": [200000, 195000, 190000, 185000, 180000]})
        
        if st.button("⭐ Add to Favorites"):
            st.toast("Added to favorites!")
        if st.button("📋 Add to Pipeline"):
            st.toast("Added to pipeline!")
        if st.button("🔔 Set Price Alert"):
            st.toast("Price alert set!")
    
    detail_modal()

# dialogs/compare_listings.py
import streamlit as st
import pandas as pd

def show_compare_modal(listing_ids: list):
    """Show side-by-side comparison of 2-4 listings."""
    @st.dialog("⚖️ Comparative Analysis", width="large")
    def compare_modal():
        st.header("⚖️ Comparative Market Analysis (CMA)")
        
        data = pd.DataFrame({
            'Feature': ['Preço', 'Área', 'Quartos', 'Score', 'Discount', 'Preço/m²', 'Valor Justo', 'Diff vs Comp 1'],
            'Imóvel 1': ['€180k', '85m²', '3', '9.2', '25%', '€2,118', '€240k', '—'],
            'Imóvel 2': ['€210k', '65m²', '2', '8.7', '19%', '€3,231', '€260k', '+€30k'],
            'Imóvel 3': ['€195k', '95m²', '4', '8.5', '17%', '€2,053', '€235k', '+€15k']
        })
        st.dataframe(data.set_index('Feature'), use_container_width=True)
        
        # Highlight best value
        st.success("🏆 **Best Value:** Imóvel 3 — maior área, menor preço/m², score alto")
    
    compare_modal()
```

---

## 22. GRÁFICOS E VISUALIZAÇÕES ENTERPRISE

### 21.1 Plotly Chart Gallery (40+ tipos aplicáveis)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CHART GALLERY — PLOTLY ENTERPRISE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CHARTS BÁSICOS (usados no dashboard)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Bar: Comparativo de categorias (preço por freguesia, counts)       │   │
│  │ Line: Tendências temporais (evolução preço, volume listings)      │   │
│  │ Scatter: Correlações (preço vs valor_justo, score vs discount)    │   │
│  │ Area: Acumulativo / preenchido (timeline de novos listings)       │   │
│  │ Pie/Donut: Distribuição proporcional (classificação de scores)   │   │
│  │ Funnel: Pipeline de negócios (detectado → contactado → fechado)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHARTS AVANÇADOS (Market Intelligence, Investment)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Candlestick: OHLC para análise de preços (se disponível dados)       │   │
│  │ Waterfall: Decomposição de valor (preço → valor_justo → discount)  │   │
│  │ Treemap: Hierarquia de valores (concelho → freguesia → tipologia)   │   │
│  │ Sunburst: Hierarquia radial (mesma info, visual diferente)         │   │
│  │ Sankey: Fluxo de listings (raw → clean → valued → scored → notif) │   │
│  │ Radar/Spider: Profile multi-dimensão (listing: score por factor)    │   │
│  │ Heatmap: Matriz de correlação (freguesia × tipologia → preço/m²)    │   │
│  │ Imshow: Heatmap de densidade geográfica (PyDeck hexagon layer)     │   │
│  │ Violin: Distribuição de preços com kernel density                   │   │
│  │ Box: Distribuição com outliers (preço por freguesia)               │   │
│  │ 3D Scatter: Preço × Área × Score (interactividade 3D)              │   │
│  │ Contour: Zonas de igual valor no mapa (contour lines de preço)     │   │
│  │ Bubble Map: Mapa com tamanho = área, cor = score                     │   │
│  │ Choropleth: Mapa coroplético (preço médio por freguesia)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EXPORT DE GRÁFICOS                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PNG (raster): Para emails, documentos, apresentações                 │   │
│  │ SVG (vector): Para impressão, escalável sem perda                   │   │
│  │ PDF: Para relatórios formais                                       │   │
│  │ HTML: Embed em páginas web                                          │   │
│  │ JSON: Dados para re-renderização                                    │   │
│  │ Interactividade: Zoom, pan, lasso select, hover tooltips           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 22. PERFORMANCE & UX

### 22.1 Performance Targets (SLA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PERFORMANCE SLA — DASHBOARD ENTERPRISE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LATÊNCIA (Time to First Meaningful Paint)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Overview (Command Center):      < 2s (KPIs + top 5 + mapa)        │   │
│  │ Search & Discovery:              < 3s (sem filtros), < 5s (com)     │   │
│  │ Listing Detail (dialog):         < 0.5s (dados já carregados)     │   │
│  │ Market Intelligence:             < 3s (INE data cached)             │   │
│  │ Investment Analytics:            < 2s (calculadora local)           │   │
│  │ System & DevOps:                 < 2s (logs paginados)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  THROUGHPUT (Renderização de Tabelas)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ st.dataframe nativo: 1000 rows < 1s | 5000 rows < 3s               │   │
│  │ AGGrid (Pro): 10000 rows < 2s (virtual scrolling)                  │   │
│  │ Pagination recomendado: 25-50 rows por página                    │   │
│  │ Lazy loading: Só renderizar rows visíveis (AGGrid)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CACHE STRATEGY (st.cache_data / st.cache_resource)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ KPIs:          TTL 60s  (frescura vs performance)                  │   │
│  │ Top listings:  TTL 300s (5 minutos)                                │   │
│  │ Search results:TTL 300s (filtros iguais = cache hit)              │   │
│  │ Market data:   TTL 3600s (1 hora — INE data muda pouco)           │   │
│  │ Price history: TTL 86400s (24h — histórico estático)              │   │
│  │ Config:        TTL ∞ (só invalidar manualmente)                   │   │
│  │ Manual invalidation: st.cache_data.clear() em "Force Refresh"     │   │
│  │ Cache hit ratio target: > 85%                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REAL-TIME UPDATES                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Polling: st.rerun() a cada 30s na Overview (configurável)          │   │
│  │ Fragments: st.fragment() para atualizar só parte da UI             │   │
│  │ WebSocket (Pro): Push de updates em tempo real via FastAPI         │   │
│  │ Background refresh: Dados atualizam em background, UI notifica    │   │
│  │ st.toast(): Notificação não-intrusiva de novos dados               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UX PATTERNS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Skeleton loading: Placeholders cinzentos enquanto dados carregam    │   │
│  │ Progressive disclosure: Mostrar detalhes só quando relevante     │   │
│  │ Empty states: Mensagens amigáveis quando não há dados              │   │
│  │ Error boundaries: Fallback UI quando componente falha              │   │
│  │ Confirmation dialogs: Para acções destrutivas (delete, reset)    │   │
│  │ Undo: Possibilidade de desfazer (favoritos, pipeline changes)    │   │
│  │ Keyboard shortcuts: Ctrl+K (search), Ctrl+D (dark mode), Esc (close)│   │
│  │ Onboarding tour: Guia passo-a-passo no primeiro acesso              │   │
│  │ Tooltips: Explicações em hover para métricas e scores             │   │
│  │ Mobile responsive: Layout de 1 coluna em ecrãs < 768px           │   │
│  │ Dark mode: Suporte nativo via st.set_page_config theme           │   │
│  │ Reduced motion: Respeitar prefers-reduced-motion                  │   │
│  │ Accessibility: ARIA labels, color contrast WCAG AA                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 23. DEPLOYMENT & ACESSIBILIDADE

### 23.1 Deployment Options

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DEPLOYMENT MATRIX — MVP → ENTERPRISE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIER 1: LOCAL (MVP)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Command: streamlit run dashboard/app.py                              │   │
│  │ URL: http://localhost:8501                                           │   │
│  │ Data: SQLite local                                                  │   │
│  │ Auth: Não (single user)                                             │   │
│  │ Cost: €0                                                            │   │
│  │ Limitations: PC precisa estar ligado, não acessível remotamente     │   │
│  │ Setup: pip install -r requirements.txt → streamlit run app.py      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIER 2: VPS (Production)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Command: streamlit run dashboard/app.py --server.port 8501         │   │
│  │ URL: https://realestate.yourdomain.com (via Nginx reverse proxy)   │   │
│  │ Data: PostgreSQL no mesmo VPS                                       │   │
│  │ Auth: HTTP Basic Auth ou JWT simples                               │   │
│  │ Cost: €20-30/mês (Hetzner, DigitalOcean)                            │   │
│  │ SSL: Certbot (Let's Encrypt) auto-renew                            │   │
│  │ Process: Systemd service com auto-restart                            │   │
│  │ Limitations: Single instance, no horizontal scaling                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIER 3: CONTAINER (Docker)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Dockerfile: python:3.11-slim + requirements + app                   │   │
│  │ docker-compose: Streamlit + PostgreSQL + Redis (cache)              │   │
│  │ Orchestration: Docker Swarm ou Kubernetes (lightweight)             │   │
│  │ Reverse Proxy: Traefik (auto SSL, load balancing)                 │   │
│  │ Scaling: 2-3 replicas para high availability                         │   │
│  │ Cost: €50-100/mês                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIER 4: CLOUD-NATIVE (Enterprise)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Platform: AWS ECS / Azure Container Apps / GCP Cloud Run           │   │
│  │ Database: AWS RDS PostgreSQL / Azure Database / Cloud SQL           │   │
│  │ Cache: ElastiCache Redis / Azure Cache / Memorystore               │   │
│  │ CDN: CloudFront / CloudFlare para assets estáticos                  │   │
│  │ Auth: Cognito / Azure AD / Firebase Auth                           │   │
│  │ Monitoring: CloudWatch / Azure Monitor / Cloud Monitoring           │   │
│  │ CI/CD: GitHub Actions → ECR → ECS deploy                            │   │
│  │ Auto-scaling: Horizontal pod autoscaling baseado em CPU/memory      │   │
│  │ Cost: €200-500/mês (depende do tráfego)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 23.2 Environment Configuration

```toml
# .streamlit/config.toml
[theme]
base = "light"  # or "dark"
primaryColor = "#1E88E5"
backgroundColor = "#FAFAFA"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#212121"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 50

[browser]
gatherUsageStats = false

[logger]
level = "info"

[runner]
magicEnabled = true
fastRerunEnabled = true
```

### 23.3 Auto-refresh & Real-time Patterns

```python
# utils/realtime.py
import streamlit as st
import time
from datetime import datetime

def auto_refresh(interval_seconds: int = 30):
    """Setup auto-refresh com countdown indicator."""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    elapsed = (datetime.now() - st.session_state.last_refresh).total_seconds()
    remaining = max(0, interval_seconds - elapsed)
    
    # Show countdown in sidebar
    with st.sidebar:
        st.progress(1 - (remaining / interval_seconds), 
                   text=f"⏱️ Refresh em {int(remaining)}s")
        if st.button("🔄 Refresh Now"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    if remaining <= 0:
        st.session_state.last_refresh = datetime.now()
        st.rerun()

def show_fresh_indicator(timestamp: datetime):
    """Show green dot if data is fresh (< 5 min), yellow if < 30 min, red otherwise."""
    age_minutes = (datetime.now() - timestamp).total_seconds() / 60
    if age_minutes < 5:
        st.markdown("🟢 **Dados frescos** (atualizados há < 5 min)")
    elif age_minutes < 30:
        st.markdown("🟡 **Dados razoáveis** (atualizados há < 30 min)")
    else:
        st.markdown("🔴 **Dados desatualizados** — clique 🔄 Refresh")
```

---

## APÊNDICE A: NOVAS PÁGINAS PROFISSIONAIS (Resumo)

### A.1 Página: Listing Detail View (Modal)
- **Trigger:** Click em qualquer listing em Search, Overview, ou Map
- **Conteúdo:** Fotos, descrição completa, valuation breakdown, score breakdown, mapa, price history, comparáveis, botões de acção (favorito, pipeline, alerta)
- **UI:** `st.dialog()` com width="large"

### A.2 Página: Comparative Analysis (Modal)
- **Trigger:** Selecionar 2-4 listings em Search → "Comparar"
- **Conteúdo:** Tabela lado-a-lado de features, gráfico radar de scores, mapa com todos os imóveis, recomendação automática de "best value"
- **UI:** `st.dialog()` com width="large"

### A.3 Página: Investment Analytics
- **Conteúdo:** Calculadoras de ROI, yield, cash flow, hipoteca, cap rate, IRR; amortization schedule; rental yield map; sensitivity analysis
- **UI:** Tabs para cada calculadora, inputs com defaults do Config, resultados em cards e gráficos

### A.4 Página: Deal Pipeline & CRM
- **Conteúdo:** Kanban board (5 stages), notas por imóvel, documentos anexados, calendar de visitas, route planner para múltiplas visitas
- **UI:** AGGrid para lista, columns para kanban, st.date_input para calendar

### A.5 Página: Favorites & Watchlist
- **Conteúdo:** Lista de favoritos, price alerts configurados, watchlist (notificar quando condições mudam), tags personalizadas
- **UI:** Cards de favoritos, toggle alerts, tag input

### A.6 Página: Price Intelligence
- **Conteúdo:** Price history por listing, price drop detection, market velocity (dias até venda), price per m² benchmarking, overpricing alerts
- **UI:** Line charts com annotations, scatter de price vs days on market

### A.7 Página: Neighborhood Deep Dive
- **Conteúdo:** Amenidades (escolas, metro, hospitais, comércio), safety scores, walkability, transit scores, future development plans, school ratings
- **UI:** Mapa com layers de POIs, radar chart de amenidades

### A.8 Página: Data Quality & Diagnostics
- **Conteúdo:** Data quality score, missing data analysis, duplicate detection, outlier visualization, data lineage, repair tools
- **UI:** Quality dashboard com gauges, drill-down por componente

---

## 25. GLOSSÁRIO DE DASHBOARD ENTERPRISE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE DASHBOARD ENTERPRISE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STREAMLIT: Framework Python para data apps (v1.42+ com dialogs, fragments) │
│  PLOTLY: Biblioteca de gráficos interactivos (40+ tipos, export PNG/SVG)   │
│  FOLIUM: Mapas 2D interactivos (OpenStreetMap, markers, clusters, heatmaps)│
│  PYDECK: Mapas 3D GPU-acelerados (Deck.gl, hexagon layers, scatter plots) │
│  PANDAS: Manipulação de dataframes (vectorização, aggregation)            │
│  AGGRID: Data grid avançado (sorting, filtering, grouping, pivoting)      │
│  FASTAPI: Framework API async para backend lightweight                    │
│                                                                             │
│  KPI: Key Performance Indicator — métrica principal de negócio             │
│  COMMAND CENTER: Página principal com visão unificada de todos os KPIs      │
│  SIDEBAR: Barra lateral de navegação persistente                          │
│  MULTI-PAGE: App com múltiplas páginas via st.navigation                 │
│  DIALOG/MODAL: Janela popup para detalhes sem sair da página             │
│  FRAGMENT: Parte de UI que pode atualizar sem rerun completo             │
│                                                                             │
│  AUTO-REFRESH: Atualização automática da página a intervalos regulares     │
│  POLLING: Verificar novos dados periodicamente (pull model)               │
│  WEBSOCKET: Comunicação bidireccional em tempo real (push model)          │
│  CACHE_DATA: Cache de resultados de funções (st.cache_data)                │
│  CACHE_RESOURCE: Cache de objectos pesados (conexões, modelos)            │
│  TTL: Time To Live — tempo de validade do cache                            │
│  CACHE INVALIDATION: Limpar cache manualmente (st.cache_data.clear())     │
│                                                                             │
│  DARK MODE: Tema escuro para uso noturno/reduzir eye strain             │
│  RESPONSIVE: Adaptação do layout ao tamanho do ecrã                      │
│  ACCESSIBILITY (A11Y): Acessibilidade para utilizadores com deficiências │
│  WCAG: Web Content Accessibility Guidelines (padrão de acessibilidade)     │
│  ARIA: Accessible Rich Internet Applications (atributos semânticos)       │
│                                                                             │
│  THROUGHPUT: Volume de dados processados por unidade de tempo              │
│  LATENCY: Tempo de resposta / atraso entre pedido e resposta              │
│  TTFB: Time To First Byte — tempo até primeiro byte de resposta          │
│  FMP: First Meaningful Paint — tempo até conteúdo útil visível          │
│  SLA: Service Level Agreement — acordo de nível de serviço               │
│                                                                             │
│  CDN: Content Delivery Network — distribuição de conteúdo geográfica     │
│  VPS: Virtual Private Server — servidor virtual na cloud                  │
│  CONTAINER: Unidade de deployment isolada (Docker)                         │
│  ORCHESTRATION: Gestão automática de containers (Kubernetes, Swarm)       │
│  REVERSE PROXY: Servidor intermediário (Nginx, Traefik)                  │
│  SSL/TLS: Encriptação de comunicação HTTPS                                │
│  CERTBOT: Cliente Let's Encrypt para certificados SSL gratuitos          │
│  SYSTEMD: System and Service Manager Linux (auto-start, auto-restart)   │
│                                                                             │
│  CMA: Comparative Market Analysis — análise comparativa de mercado         │
│  ARV: After Repair Value — valor após renovação                          │
│  NOI: Net Operating Income — rendimento líquido de operações             │
│  CAP RATE: Capitalization Rate — taxa de capitalização (NOI / Price)      │
│  CASH-ON-CASH: Retorno anual sobre investimento em cash                  │
│  IRR: Internal Rate of Return — taxa interna de retorno                  │
│  ROI: Return on Investment — retorno sobre investimento                  │
│  YIELD: Rendimento (renda anual / preço de compra)                       │
│  LTV: Loan To Value — rácio empréstimo / valor do imóvel                 │
│  DSCR: Debt Service Coverage Ratio — cobertura de serviço da dívida      │
│                                                                             │
│  PIPELINE: Sequência de processos (scraping → ETL → valuation → scoring)   │
│  KANBAN: Sistema visual de gestão de tarefas (To Do → Doing → Done)        │
│  CRM: Customer Relationship Management — gestão de relacionamento          │
│  WATCHLIST: Lista de vigilância (alertas quando condições mudam)         │
│  PRICE DROP: Redução de preço de um listing ao longo do tempo           │
│  MARKET VELOCITY: Velocidade de mercado (tempo médio até venda)          │
│  SEASONALITY: Padrão sazonal de preços/volume ao longo do ano            │
│  FORECASTING: Previsão de valores futuros com modelos ML/estatísticos   │
│  CONFIDENCE INTERVAL: Intervalo de confiança (ex: 80% CI)                 │
│  SHAP: SHapley Additive exPlanations — explicabilidade de modelos ML     │
│                                                                             │
│  ETL: Extract, Transform, Load — pipeline de processamento de dados      │
│  DEDUPLICATION: Eliminação de registos duplicados                         │
│  GEOCODING: Conversão de endereço em coordenadas lat/lon                   │
│  ENRICHMENT: Adição de dados externos (INE, POIs) ao dataset             │
│  NORMALIZATION: Conversão de dados brutos para formato padrão            │
│  VALIDATION: Verificação de qualidade e integridade dos dados            │
│                                                                             │
│  RED FLAG: Indicador de alerta (overpricing, suspeito, localização)     │
│  RATIONALE: Justificação textual do score (porquê este imóvel é bom?)    │
│  DISCOUNT: Diferença percentual entre preço pedido e valor justo           │
│  FRESHNESS: Idade do anúncio (quanto mais recente, melhor)                │
│  LIQUIDITY: Facilidade de venda (volume, tempo no mercado)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 25. DARK-MODE FIX (ONDA 3) & AI DEALS VIEW

### 25.1 Dark-Mode Fix (Onda 3)

**Problema:**
- Cores claras hardcoded em `overview.py` e `scraping_results.py` ficavam ilegíveis em dark mode
- `.streamlit/config.toml` estava configurado com base "light"
- Tabelas renderizadas via canvas não respeitavam o tema dark

**Solução:**
- Alterar `.streamlit/config.toml` base para "dark"
- Remover cores claras hardcoded e substituir por variantes dark
- Ajustar fundo de inner-box para cor escura consistente com tema

**Implementação:**
```toml
# .streamlit/config.toml
[theme]
base="dark"
primaryColor="#F63366"
backgroundColor="#0E1117"
secondaryBackgroundColor="#262730"
textColor="#FAFAFA"
font="sans serif"
```

```python
# realestate_engine/dashboard/views/overview.py
# Antes (cor clara hardcoded)
st.markdown(f"""
<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
    ...
</div>
""", unsafe_allow_html=True)

# Depois (variante dark)
st.markdown(f"""
<div style="background-color: #262730; padding: 10px; border-radius: 5px;">
    ...
</div>
""", unsafe_allow_html=True)
```

### 25.2 AI Deals View (LLM-Powered Opportunity Analysis)

**Nova View:**
- View "AI Deals" powered por Ollama local (mistral:7b)
- Análise LLM de oportunidades de investimento
- Gera rationale detalhado para cada deal
- Integração com OpportunityAnalyzer

**Funcionalidades:**
- Top 3-5 deals analisados por LLM
- Rationale natural language explicando porquê cada deal é bom
- Insights sobre potencial de valorização
- Comparação com comparáveis de mercado

**Implementação:**
```python
# realestate_engine/dashboard/views/ai_deals.py
from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer

async def show_ai_deals():
    analyzer = OpportunityAnalyzer(provider="ollama")
    deals = await analyzer.get_top_deals_report(limit=5)
    
    for deal in deals:
        st.markdown(f"### {deal['title']}")
        st.markdown(f"**Score:** {deal['score']}/10")
        st.markdown(f"**Preço:** {deal['price']}€")
        st.markdown(f"**Valor Justo:** {deal['fair_value']}€")
        st.markdown(f"**Discount:** {deal['discount']}%")
        st.markdown("---")
        st.markdown(f"**Análise LLM:**")
        st.markdown(deal['rationale'])
```

### 25.3 Lista Completa de Views Implementadas

**15 Views Atuais:**
1. Overview / Command Center
2. Search & Discovery
3. Watchlist
4. Map View
5. AI Deals (LLM-powered)
6. Market Analysis
7. Investor Tools
8. Score Audit
9. Pipeline Status
10. Scraping Results
11. Data Quality
12. System
13. Config
14. Telegram
15. Debug Logs

---

*Fim do Documento 10 — Dashboard Streamlit Profissional (v6.0 Enterprise)*
*Benchmarks: Zillow, Redfin, Idealista Pro, Rentana, CoStar, AirDNA, PropStream*
*Total de Views Implementadas: 15 views*
*Atualizado com Dark-Mode Fix (Onda 3) e AI Deals View*
