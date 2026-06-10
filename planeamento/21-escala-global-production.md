# ESCALA GLOBAL — REAL ESTATE OPPORTUNITY ENGINE
## Roadmap para Production-Grade: Local → Global

> **Este documento:** Roadmap estratégico para escalar o sistema de local para global
> **Objectivo:** Fornecer roadmap acionável para transformar o baseline local em sistema production-grade
> **Versão:** 1.0 (Criado 2026-04-30)
> **Pré-requisito:** Baseline production-ready (Ondas 1-5 completas)

---

## ÍNDICE

1. [Introdução — Por que Escalar?](#1-introdução-por-que-escalar)
2. [Proxy Rotation & Anti-Detection](#2-proxy-rotation-anti-detection)
3. [Database Scaling](#3-database-scaling)
4. [LLM Provider Strategy](#4-llm-provider-strategy)
5. [Cloud Deployment](#5-cloud-deployment)
6. [Monitoring & Observability](#6-monitoring-observability)
7. [Security Hardening](#7-security-hardening)
8. [Cost Optimization](#8-cost-optimization)
9. [Roadmap de Implementação](#9-roadmap-de-implementacao)
10. [Glossário de Escala Global](#10-glossario-de-escala-global)

---

## 1. INTRODUÇÃO — POR QUE ESCALAR?

### 1.1 Limitações do Baseline Local

O baseline atual (Ondas 1-5) é production-ready para uso local single-user:
- **SQLite**: Single-writer DB, sem replicação, sem backup automático
- **Ollama local**: CPU-bound, sem escalabilidade, cold-start lento
- **Proxies estáticos**: Risco de banimento, sem rotação
- **Scripts manuais**: `start.bat` / `start.sh`, sem automação cloud
- **Monitoring básico**: Loguru + Prometheus metrics locais

**Limitações:**
- Não suporta múltiplos utilizadores simultâneos
- Single point of failure (DB local)
- Difícil de escalar para novos mercados/países
- Sem alta disponibilidade (HA)
- Sem disaster recovery (DR)

### 1.2 Casos de Uso de Escala Global

**Caso A: Multi-Investor SaaS**
- Múltiplos utilizadores com permissões diferenciadas
- Cada utilizador vê apenas os seus favoritos/alertas
- Escala: 10-100 utilizadores simultâneos

**Caso B: Expansão Geográfica**
- Escalar de Portugal para Espanha, França, Itália
- Proxies geolocalizados por país
- Modelos de valuation adaptados a cada mercado
- Escala: 3-5 países

**Caso C: Alta Disponibilidade 24/7**
- Deploy em multiple AZs (availability zones)
- Failover automático
- Backup e restore automatizados
- Escala: 99.9% uptime

### 1.3 Trade-offs: Custo vs Benefício

| Componente | Local (Baseline) | Global (Production) | Custo Extra | Benefício |
|---|---|---|---|---|
| Database | SQLite local | PostgreSQL + replicas | $50-200/mês | HA, backup, multi-user |
| LLM | Ollama local | OpenAI API / Azure | $100-500/mês | Velocidade, qualidade |
| Proxies | Estáticos | Pool rotativo | $100-300/mês | Anti-ban, escalabilidade |
| Deployment | Scripts manuais | K8s + CI/CD | $200-500/mês | Automatização, HA |
| Monitoring | Local | Centralizado (ELK) | $50-150/mês | Observabilidade, alerting |
| **Total** | **$0** | **$500-1650/mês** | **$500-1650** | **Multi-user, HA, escala** |

---

## 2. PROXY ROTATION & ANTI-DETECTION

### 2.1 Estado Atual

**Baseline:**
- Proxies estáticos definidos em `config.py`
- Sem rotação automática
- Sem health checks
- Risco de banimento se um proxy é blacklisted

**Limitações:**
- Portais podem detectar IPs fixos
- Sem redundância se proxy falha
- Difícil de escalar para muitos portais/países

### 2.2 Escala Global Necessária

**Proxy Pool Rotativo:**
- **Residential proxies**: IPs reais de utilizadores finais (menor risco de ban)
- **Datacenter proxies**: Mais baratos, maior risco de detecção
- **Mix estratégico**: 70% residential + 30% datacenter

**Geolocation Targeting:**
- Portugal: proxies portugueses
- Espanha: proxies espanhóis
- França: proxies franceses
- Fallback: proxies da UE se específico não disponível

**Rate Limiting per-Portal:**
- Cada portal tem limites diferentes (ex: Idealista 100 req/h)
- Rotator respeita limites per-portal
- Backoff exponencial em caso de 429

**Proxy Health Checks:**
- Ping check: proxy responde?
- HTTP check: proxy faz requests com sucesso?
- Geolocation check: IP está no país esperado?
- Auto-rotation: remove proxies mortos do pool

### 2.3 Implementação Sugerida

**Novo Componente: `ProxyRotator`**

```python
# realestate_engine/scraping/proxy_rotator.py
class ProxyRotator:
    """Gerencia pool de proxies com rotação e health checks."""
    
    def __init__(self, provider: str = "brightdata"):  # brightdata, oxylabs, smartproxy
        self.pool = self._load_pool(provider)
        self.health_cache = {}
        
    def get_proxy(self, portal: str, country: str = "PT") -> dict:
        """Retorna proxy saudável para o portal/país."""
        candidates = [p for p in self.pool if p.country == country and p.portal_allowed(portal)]
        return self._select_healthy(candidates)
    
    def mark_failed(self, proxy: dict, reason: str):
        """Marca proxy como falhado temporariamente."""
        proxy.failed_until = datetime.now() + timedelta(minutes=30)
        
    def health_check_loop(self):
        """Background loop que verifica saúde do pool."""
        while True:
            for proxy in self.pool:
                if self._is_healthy(proxy):
                    proxy.healthy = True
                else:
                    proxy.healthy = False
            sleep(300)  # 5 min entre checks
```

**Integração com SpiderManager:**
```python
# realestate_engine/scraping/spider_manager.py
class SpiderManager:
    def __init__(self):
        self.proxy_rotator = ProxyRotator()
        
    async def run_all_cycle(self, active_portals: list):
        for portal in active_portals:
            proxy = self.proxy_rotator.get_proxy(portal, country="PT")
            try:
                await self._run_spider(portal, proxy)
            except Exception as e:
                self.proxy_rotator.mark_failed(proxy, str(e))
```

**Providers Sugeridos:**
- Bright Data (Luminati): Premium, residential, caro
- Oxylabs: Bom balanço preço/qualidade
- Smartproxy: Entry-level, bom para começar
- Self-hosted: Proxies próprias (se tiver infraestrutura)

**Custo Estimado:**
- Residential: $3-10/GB
- Datacenter: $0.5-2/GB
- Para scraping moderado (10GB/mês): $50-200/mês

---

## 3. DATABASE SCALING

### 3.1 Estado Atual

**Baseline:**
- SQLite local (`data/db/realestate.db`)
- Single-writer, single-reader
- Sem replicação
- Backup manual (scripts ocasionais)

**Limitações:**
- Não suporta múltiplos escritores simultâneos
- Sem HA (single point of failure)
- Sem backup automatizado
- Performance degrada com >100k listings

### 3.2 Escala Global Necessária

**PostgreSQL (Managed):**
- AWS RDS / Google Cloud SQL / Azure Database
- Multi-AZ deployment (primary + standby)
- Automatic backups (7-30 dias retention)
- Point-in-time recovery (PITR)
- Read replicas para queries de dashboard

**Connection Pooling:**
- PgBouncer para gerenciar conexões
- Reduz overhead de conexões
- Melhora throughput

**Migrations:**
- Alembic já existe em `database/migrations/`
- Adaptar para PostgreSQL (diferenças de tipos)
- Zero-downtime migrations

### 3.3 Implementação Sugerida

**Configuração:**
```env
# .env (production)
DATABASE_URL=postgresql://user:pass@host:5432/realestate
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_READ_REPLICA_URL=postgresql://readonly:pass@replica-host:5432/realestate
```

**Código:**
```python
# realestate_engine/database/models.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # verifica conexões antes de usar
)

# Para dashboard queries (read-only)
read_engine = create_async_engine(DATABASE_READ_REPLICA_URL)
```

**Backup Strategy:**
- Automated daily backups (RDS automated backups)
- Weekly snapshots para long-term retention
- Cross-region replication para DR
- Restore drills trimestrais

**Custo Estimado (AWS RDS):**
- db.t3.medium (2 vCPU, 4GB RAM): $50-100/mês
- Multi-AZ: +50%
- Read replica: +50%
- Storage (100GB): $10/mês
- **Total: $100-200/mês**

---

## 4. LLM PROVIDER STRATEGY

### 4.1 Estado Atual

**Baseline:**
- Ollama local (`mistral:7b`)
- CPU-bound, cold-start lento
- Sem redundância
- Modelo fixo

**Limitações:**
- Cold-start 30-60s em CPU
- Qualidade inferior a GPT-4
- Sem escalabilidade
- Single point of failure

### 4.2 Escala Global Necessária

**OpenAI API (GPT-4):**
- Qualidade superior
- Baixa latência
- Escalabilidade infinita
- Custo por token

**Alternativas:**
- Azure OpenAI (mesmos modelos, compliance enterprise)
- Anthropic Claude (Claude 3 Opus/Sonnet)
- Google Vertex AI (Gemini)
- Fallback local (Ollama) para redução de custos

**Hybrid Strategy:**
- **Production**: OpenAI GPT-4 para AI Deals críticos
- **Staging**: Claude 3 Sonnet (mais barato)
- **Fallback**: Ollama local se API falha
- **Batch jobs**: Ollama para análises não-críticas (reduz custo)

### 4.3 Implementação Sugerida

**Abstração LLMProvider:**
```python
# realestate_engine/investor_tools/llm_provider.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_deal(self, listing: dict) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
    async def analyze_deal(self, listing: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[...]
        )
        return response.choices[0].message.content

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "mistral:7b"):
        self.host = host
        self.model = model
        
    async def analyze_deal(self, listing: dict) -> str:
        # Ollama implementation
        pass

class HybridProvider(LLMProvider):
    """Tenta OpenAI, fallback para Ollama."""
    def __init__(self):
        self.primary = OpenAIProvider(...)
        self.fallback = OllamaProvider(...)
        
    async def analyze_deal(self, listing: dict) -> str:
        try:
            return await self.primary.analyze_deal(listing)
        except Exception:
            logger.warning("OpenAI failed, falling back to Ollama")
            return await self.fallback.analyze_deal(listing)
```

**Configuração:**
```env
# .env (production)
LLM_PROVIDER=openai  # openai, azure, anthropic, ollama, hybrid
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

**Custo Estimado:**
- OpenAI GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
- Para 1000 análises/mês (10K tokens cada): $600-900/mês
- Ollama local: $0 (custo de infraestrutura apenas)
- Hybrid (70% Ollama, 30% OpenAI): $200-300/mês

---

## 5. CLOUD DEPLOYMENT

### 5.1 Estado Atual

**Baseline:**
- Windows/macOS local
- Scripts manuais (`start.bat` / `start.sh`)
- Sem automação
- Sem CI/CD

**Limitações:**
- Deploy manual
- Sem rollback automático
- Sem escalabilidade horizontal
- Sem multi-environment (dev/staging/prod)

### 5.2 Escala Global Necessária

**Docker Containers:**
- App container (FastAPI + Streamlit + Scheduler)
- DB container (PostgreSQL)
- Ollama container (opcional, para fallback)
- Nginx container (reverse proxy + SSL)

**Orchestration:**
- **Staging**: Docker Compose (simples, barato)
- **Production**: Kubernetes (escalável, HA)

**CI/CD Pipeline:**
- GitHub Actions / GitLab CI
- Automatic build on push
- Automatic deploy to staging
- Manual approval para production
- Rollback automático em caso de falha

**Infrastructure as Code:**
- Terraform já existe em `terraform/`
- Expandir para provisioning completo
- State management remoto (S3)

### 5.3 Implementação Sugerida

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY realestate_engine/ .
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "-m", "realestate_engine.main_engine"]
```

**Docker Compose (Staging):**
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/realestate
    depends_on:
      - db
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=realestate
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - db_data:/var/lib/postgresql/data
      
volumes:
  db_data:
```

**Kubernetes (Production):**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realestate-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: realestate-engine
  template:
    metadata:
      labels:
        app: realestate-engine
    spec:
      containers:
      - name: app
        image: realestate-engine:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
```

**CI/CD (GitHub Actions):**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t realestate-engine .
      - name: Push to registry
        run: docker push ...
      - name: Deploy to staging
        run: kubectl apply -f k8s/staging/
        
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    steps:
      - name: Deploy to production
        run: kubectl apply -f k8s/production/
```

**Custo Estimado:**
- Docker Compose (VPS): $20-50/mês
- Kubernetes (EKS/GKE): $200-500/mês
- CI/CD (GitHub Actions): Free para público, $20-100/mês para privado
- **Total: $220-650/mês**

---

## 6. MONITORING & OBSERVABILITY

### 6.1 Estado Atual

**Baseline:**
- Loguru (local logs)
- Prometheus metrics básicas
- Health checks locais
- Sem centralização

**Limitações:**
- Logs dispersos em múltiplas máquinas
- Sem alerting
- Sem tracing distribuído
- Difícil debug de issues em produção

### 6.2 Escala Global Necessária

**Centralized Logging:**
- ELK Stack (Elasticsearch + Logstash + Kibana)
- Ou Loki + Grafana (mais leve)
- Logs de todos os containers num único lugar
- Full-text search e filtragem

**Distributed Tracing:**
- OpenTelemetry
- Trace requests end-to-end (scraping → ETL → valuation → scoring)
- Identificar bottlenecks

**Alerting:**
- PagerDuty / OpsGenie / Slack
- Alertas baseados em SLOs
- Escalation policies

**SLOs e Error Budgets:**
- SLO: 99.9% uptime
- Error budget: 43min/mês
- Alertas quando error budget é consumido

### 6.3 Implementação Sugerida

**OpenTelemetry Integration:**
```python
# realestate_engine/monitoring/otel.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger import JaegerExporter

tracer = trace.get_tracer(__name__)

FastAPIInstrumentor.instrument_app(app)
```

**Grafana Dashboards:**
- Dashboard de scraping (success rate, latency, errors per portal)
- Dashboard de ETL (throughput, backlog, quality metrics)
- Dashboard de valuation (model performance, drift)
- Dashboard de sistema (CPU, memory, disk, network)

**Alert Rules:**
```yaml
# alerting_rules.yml
groups:
  - name: scraping
    rules:
      - alert: ScrapingFailureRateHigh
        expr: rate(scraping_errors[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Taxa de falhas de scraping > 10%"
```

**Custo Estimado:**
- ELK Stack (self-hosted): $100-200/mês
- Loki + Grafana Cloud: $50-150/mês
- Jaeger (self-hosted): $50-100/mês
- PagerDuty: $20-50/mês
- **Total: $120-400/mês**

---

## 7. SECURITY HARDENING

### 7.1 Estado Atual

**Baseline:**
- `.env` local (não versionado)
- Rate limiting básico (FastAPI)
- Input validation
- Sem secrets management
- Sem WAF

**Limitações:**
- Secrets em plaintext no servidor
- Sem proteção contra DDoS
- Sem audit logging
- Risco de credential leakage

### 7.2 Escala Global Necessária

**Secrets Management:**
- AWS Secrets Manager / HashiCorp Vault
- Rotação automática de secrets
- Audit logging de acesso

**WAF (Web Application Firewall):**
- Cloudflare WAF
- AWS WAF
- Proteção contra SQL injection, XSS, DDoS

**DDoS Protection:**
- Cloudflare
- AWS Shield
- Rate limiting global

**Audit Logging:**
- Log de todas as ações administrativas
- Log de acesso a dados sensíveis
- Imutável (não pode ser apagado)

### 7.3 Implementação Sugerida

**AWS Secrets Manager:**
```python
# realestate_engine/utils/config.py
import boto3

secrets = boto3.client('secretsmanager')

def get_secret(secret_name: str) -> str:
    response = secrets.get_secret_value(SecretId=secret_name)
    return response['SecretString']

DATABASE_URL = get_secret('realestate/database_url')
```

**Cloudflare WAF:**
- Regras de firewall para SQL injection
- Rate limiting por IP
- Bot protection

**Audit Logging:**
```python
# realestate_engine/monitoring/audit.py
class AuditLogger:
    def log_action(self, user: str, action: str, resource: str):
        logger.info(
            f"AUDIT: user={user} action={action} resource={resource} "
            f"timestamp={datetime.now().isoformat()}",
            extra={"audit": True}
        )
```

**Custo Estimado:**
- AWS Secrets Manager: $0.40/secret/mês + $0.05/10K calls
- Cloudflare WAF (Free tier): $0
- AWS Shield Standard: $0
- AWS Shield Advanced: $3000/mês (não necessário inicialmente)
- **Total: $5-20/mês**

---

## 8. COST OPTIMIZATION

### 8.1 Estimativa de Custos por Componente

| Componente | Local | Production | Custo Extra |
|---|---|---|---|
| Database | $0 | $100-200 | $100-200 |
| LLM | $0 | $200-900 | $200-900 |
| Proxies | $0 | $50-200 | $50-200 |
| Deployment | $0 | $220-650 | $220-650 |
| Monitoring | $0 | $120-400 | $120-400 |
| Security | $0 | $5-20 | $5-20 |
| **TOTAL** | **$0** | **$495-2170** | **$495-2170** |

### 8.2 Estratégias de Otimização

**Database:**
- Usar spot instances para não-critical workloads
- Reserved instances para workload constante (30-60% desconto)
- Read replicas apenas durante horários de pico

**LLM:**
- Hybrid strategy (70% Ollama, 30% OpenAI)
- Cache de respostas (mesmo listing não precisa de nova análise)
- Batch jobs off-peak (horários mais baratos)

**Deployment:**
- Horizontal pod autoscaler (HPA)
- Scale to zero durante horários de inatividade
- Spot instances para non-critical pods

**Monitoring:**
- Retention de logs limitado (7-30 dias)
- Sampling de traces (10% em produção, 100% em staging)

### 8.3 ROI Analysis

**Custo: $495-2170/mês**

**Benefícios:**
- Multi-user SaaS: $50-100/utilizador/mês × 10 utilizadores = $500-1000/mês
- Expansão geográfica: 3× mais oportunidades = ROI 6-12 meses
- HA/DR: Evita downtime que custaria $1000+ em oportunidades perdidas
- Escala horizontal: Suporta crescimento sem refator

**Break-even:**
- Conservador: 6-12 meses
- Otimista: 3-6 meses

---

## 9. ROADMAP DE IMPLEMENTAÇÃO

### 9.1 Fase 1: PostgreSQL Migration (1-2 semanas)

**Objectivo:** Migrar de SQLite para PostgreSQL

**Tasks:**
- [ ] Configurar RDS PostgreSQL (Multi-AZ)
- [ ] Adaptar models para PostgreSQL (tipos, índices)
- [ ] Migrar dados existentes
- [ ] Testar em staging
- [ ] Switch production
- [ ] Configurar backups automatizados

**Riscos:**
- Downtime durante migration
- Dados corrompidos se migration falha

**Mitigação:**
- Migration offline (manutenção programada)
- Backup completo antes de migration
- Rollback plan documentado

### 9.2 Fase 2: Proxy Rotation (2-3 semanas)

**Objectivo:** Implementar proxy pool rotativo

**Tasks:**
- [ ] Escolher provider (Bright Data / Oxylabs / Smartproxy)
- [ ] Implementar ProxyRotator
- [ ] Integrar com SpiderManager
- [ ] Configurar health checks
- [ ] Testar com todos os portais
- [ ] Monitorar taxa de banimento

**Riscos:**
- Proxies caros
- Proxies ainda são banidos

**Mitigação:**
- Começar com provider entry-level
- Mix residential + datacenter
- Rate limiting conservador

### 9.3 Fase 3: Cloud LLM Integration (1 semana)

**Objectivo:** Implementar abstração LLMProvider com OpenAI

**Tasks:**
- [ ] Implementar LLMProvider ABC
- [ ] Implementar OpenAIProvider
- [ ] Implementar HybridProvider (OpenAI + Ollama fallback)
- [ ] Configurar API keys
- [ ] Testar qualidade vs Ollama
- [ ] Medir latência e custo

**Riscos:**
- Custo alto
- API rate limits

**Mitigação:**
- Hybrid strategy (Ollama fallback)
- Cache de respostas
- Limitar a X análises/mês

### 9.4 Fase 4: Docker + CI/CD (2 semanas)

**Objectivo:** Containerizar e automatizar deploy

**Tasks:**
- [ ] Criar Dockerfile
- [ ] Criar Docker Compose (staging)
- [ ] Configurar GitHub Actions
- [ ] Deploy automático para staging
- [ ] Testar rollback
- [ ] Documentar processo

**Riscos:**
- Container não funciona como esperado
- CI/CD pipeline falha

**Mitigação:**
- Testar Docker localmente primeiro
- Pipeline em staging antes de production

### 9.5 Fase 5: Kubernetes Deployment (3-4 semanas)

**Objectivo:** Deploy em K8s para production

**Tasks:**
- [ ] Criar cluster EKS/GKE
- [ ] Criar manifests K8s (deployment, service, ingress)
- [ ] Configurar HPA (Horizontal Pod Autoscaler)
- [ ] Configurar secrets (Kubernetes secrets)
- [ ] Deploy production
- [ ] Testar failover

**Riscos:**
- Complexidade de K8s
- Custos altos

**Mitigação:**
- Começar com cluster pequeno
- Usar managed service (EKS/GKE)
- Documentar tudo

### 9.6 Fase 6: Monitoring Completo (2 semanas)

**Objectivo:** Implementar observabilidade completa

**Tasks:**
- [ ] Configurar Loki/Grafana
- [ ] Implementar OpenTelemetry
- [ ] Criar dashboards Grafana
- [ ] Configurar alertas
- [ ] Testar alertas
- [ ] Documentar runbooks

**Riscos:**
- Overhead de instrumentação
- Alertas falsos

**Mitigação:**
- Sampling de traces
- Tuning de alertas
- Start com alertas críticos apenas

### 9.7 Timeline Total

**Conservador:** 11-14 semanas (3-4 meses)
**Otimista:** 8-10 semanas (2-3 meses)

---

## 10. GLOSSÁRIO DE ESCALA GLOBAL

- **HA (High Availability)**: Sistema que continua operacional mesmo se um componente falha
- **DR (Disaster Recovery)**: Processo de recuperar sistema após falha catastrófica
- **Multi-AZ**: Deploy em múltiplas availability zones (datacenters diferentes)
- **Read Replica**: Cópia read-only do DB para queries de leitura
- **Connection Pooling**: Reutilização de conexões DB para reduzir overhead
- **PITR (Point-in-Time Recovery)**: Capacidade de restaurar DB para qualquer momento no passado
- **SLO (Service Level Objective)**: Meta de performance/uptime (ex: 99.9% uptime)
- **Error Budget**: Tempo de downtime permitido antes de violar SLO
- **WAF (Web Application Firewall)**: Firewall que filtra tráfico HTTP malicioso
- **DDoS (Distributed Denial of Service)**: Ataque que sobrecarrega servidor com tráfego
- **Spot Instance**: Instância cloud barata que pode ser revogada pelo provider
- **Reserved Instance**: Instância cloud reservada por 1-3 anos com desconto
- **HPA (Horizontal Pod Autoscaler)**: Escala automática de pods Kubernetes baseado em CPU/memória
- **Distributed Tracing**: Rastreamento de requests através de múltiplos serviços
- **Observability**: Capacidade de entender estado interno do sistema através de logs, metrics e traces
