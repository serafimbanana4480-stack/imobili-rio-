# Índice Mestre de Documentação

Índice central de toda a documentação do projeto Real Estate Opportunity Engine.

## 📖 Documentação Principal

### Para Começar
- **[README.md](../README.md)** - Documentação principal do projeto
  - Quick start (Windows/macOS/Linux)
  - Arquitetura do sistema
  - Configuração
  - Troubleshooting

### Manuais de Uso
- **[COMO_USAR.md](COMO_USAR.md)** - Manual de utilização detalhado
- **[como_usar/](como_usar/)** - Guias rápidos para utilizadores não técnicos
  - [Manual de Uso Rápido](como_usar/Manual_de_Uso_Rapido.md)
  - [Apresentação do Projeto](como_usar/Apresentacao_do_Projeto.md)

### Documentação Técnica
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitetura técnica detalhada
- **[API.md](API.md)** - Referência da API REST
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guia de deployment
- **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)** - Configuração do Telegram
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Estrutura do projeto

## 📊 Relatórios e Auditorias

### Auditorias Recentes
- **[Auditoria Estrutural Completa](reports/AUDITORIA_ESTRUTURAL_COMPLETA_2026-05-05.md)** *(2026-05-05)*
  - Ficheiros duplicados
  - Documentação redundante
  - Problemas de naming
  - Estrutura do projeto
- **[Auditoria Independente Completa](reports/AUDITORIA_INDEPENDENTE_COMPLETA_2026-05-05.md)** *(2026-05-05)*
- **[Análise de Lacunas Completa](reports/ANALISE_LACUNAS_COMPLETA.md)**

### Production Readiness
- **[PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md)** - Auditoria de produção e roadmap
- **[Production Setup](reports/PRODUCTION_SETUP.md)**
- **[Deployment Summary](reports/DEPLOYMENT_SUMMARY.md)**

### Auditorias por Componente
- **[reports/audit/](reports/audit/)** - Auditorias detalhadas por fase
  - PHASE_01_STRUCTURAL_AUDIT.md
  - PHASE_02_SCRAPING_AUDIT.md
  - PHASE_03_ETL_DATA_QUALITY_AUDIT.md
  - PHASE_04_VALUATION_ML_AUDIT.md
  - PHASE_05_SCORING_ENGINE_AUDIT.md
  - ... (15 fases no total)

### Outros Relatórios
- **[Analysis Report](reports/ANALYSIS_REPORT.md)**
- **[GAP Analysis](reports/GAP_ANALYSIS_REPORT.md)**
- **[Optimization Report](reports/OPTIMIZATION_REPORT.md)**
- **[Verification Report](reports/VERIFICATION_REPORT.md)**

## 📋 Planeamento do Projeto

- **[../planeamento/](../planeamento/)** - Documentos de planeamento (21 ficheiros em português)
  - [01-visao-geral.md](../planeamento/01-visao-geral.md)
  - [02-mercado-imobiliario-portugal.md](../planeamento/02-mercado-imobiliario-portugal.md)
  - [03-arquitetura-sistema.md](../planeamento/03-arquitetura-sistema.md)
  - [04-scraping-nodriver-2026.md](../planeamento/04-scraping-nodriver-2026.md)
  - [05-etl-pipeline.md](../planeamento/05-etl-pipeline.md)
  - [06-valuation-engine.md](../planeamento/06-valuation-engine.md)
  - [07-scoring-engine.md](../planeamento/07-scoring-engine.md)
  - [08-database-design.md](../planeamento/08-database-design.md)
  - [09-notificacoes-telegram.md](../planeamento/09-notificacoes-telegram.md)
  - [10-dashboard-streamlit.md](../planeamento/10-dashboard-streamlit.md)
  - [11-scheduler-orchestration.md](../planeamento/11-scheduler-orchestration.md)
  - [12-monitoring-logging.md](../planeamento/12-monitoring-logging.md)
  - [13-testes-qualidade.md](../planeamento/13-testes-qualidade.md)
  - [14-deployment-local.md](../planeamento/14-deployment-local.md)
  - [15-security-gdpr.md](../planeamento/15-security-gdpr.md)
  - [16-escalabilidade-producao.md](../planeamento/16-escalabilidade-producao.md)
  - [17-estrutura-projecto.md](../planeamento/17-estrutura-projecto.md)
  - [18-roadmap-implementacao.md](../planeamento/18-roadmap-implementacao.md)
  - [19-estrategia-dados.md](../planeamento/19-estrategia-dados.md)
  - [20-guia-ia-desenvolvimento.md](../planeamento/20-guia-ia-desenvolvimento.md)
  - [21-escala-global-production.md](../planeamento/21-escala-global-production.md)

## 🔧 Scripts e Ferramentas

### Scripts de Produção
- **[../scripts/production/](../scripts/production/)** - Scripts de produção e manutenção
  - [deploy.sh](../scripts/production/deploy.sh)
  - [run_scraper_manual.py](../scripts/production/run_scraper_manual.py)
  - [run_detail_scraping.py](../scripts/production/run_detail_scraping.py)
  - [system_audit.py](../scripts/production/system_audit.py)

### Scripts de Manutenção
- **[../scripts/production/maintenance/](../scripts/production/maintenance/)**
  - [clean_db.py](../scripts/production/maintenance/clean_db.py) - Limpeza de DB consolidada

### Scripts de Verificação
- **[../scripts/production/verify/](../scripts/production/verify/)**
  - [debug_remax.py](../scripts/production/verify/debug_remax.py) - Debug REMAX consolidado

### Scripts de Debug (Arquivados)
- **[../scripts/archive/temp_debug/](../scripts/archive/temp_debug/)** - Scripts temporários arquivados

## 🧪 Testes

- **[../tests/](../tests/)** - Suíte de testes principal
  - [test_ollama_timeout_fallback.py](../tests/test_ollama_timeout_fallback.py)
  - [test_score_audit_regression.py](../tests/test_score_audit_regression.py)
  - [test_weight_validation.py](../tests/test_weight_validation.py)
  - ... (mais testes em unit/, integration/, e2e/)

## 📦 Estrutura do Projeto

```
projeto/
├── README.md                    # Documentação principal
├── PRODUCTION_READINESS.md      # Auditoria de produção
├── realestate_engine/          # Código principal
│   ├── api/                    # FastAPI REST
│   ├── dashboard/              # Streamlit UI
│   ├── scraping/               # Spiders
│   ├── etl/                    # Pipeline ETL
│   ├── valuation/              # ML valuation
│   ├── scoring/                # Scoring engine
│   └── ...
├── scripts/                     # Scripts de automação
│   ├── production/             # Scripts de produção
│   ├── archive/                # Scripts arquivados
│   └── debug/                  # Scripts de debug
├── tests/                       # Suíte de testes
├── docs/                        # Documentação
│   ├── INDEX.md                # Este índice
│   ├── README.md              # Índice de documentação
│   ├── reports/                # Relatórios e auditorias
│   └── como_usar/              # Guias rápidos
├── planeamento/                 # Documentos de planeamento
└── data/                        # Dados (DB, cache, logs)
```

## 🔗 Links Rápidos

- [Quick Start](../README.md#quick-start-windows)
- [Arquitetura](ARCHITECTURE.md)
- [API Reference](API.md)
- [Troubleshooting](../README.md#troubleshooting)
- [Production Readiness](../PRODUCTION_READINESS.md)
- [Auditoria Estrutural](reports/AUDITORIA_ESTRUTURAL_COMPLETA_2026-05-05.md)

## 📝 Política de Idiomas

- **Português**: Documentação principal, manuais de uso, planeamento
- **Inglês**: Documentação técnica detalhada, código, comentários
- **Misto**: Alguns documentos técnicos mantêm inglês para consistência com terminologia padrão

---

**Última atualização:** 2026-05-05  
**Versão:** 1.0
