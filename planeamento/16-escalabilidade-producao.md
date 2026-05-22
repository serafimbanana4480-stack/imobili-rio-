# ESCALABILIDADE E PRODUÇÃO — REAL ESTATE OPPORTUNITY ENGINE
## Escala de Local para Cloud-Native

> **Este documento:** Especificação completa de escalabilidade e produção  
> **Objectivo:** Fornecer especificação detalhada de escalabilidade para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução à Escalabilidade](#1-introducao-a-escalabilidade)
2. [Arquitectura de Escala](#2-arquitetura-de-escala)
3. [Fase 1: Local (MVP)](#3-fase-1-local-mvp)
4. [Fase 2: VPS (Produção)](#4-fase-2-vps-producao)
5. [Fase 3: Cloud-Native (Microservices)](#5-fase-3-cloud-native-microservices)
6. [Estratégia de Migração](#6-estrategia-de-migracao)
7. [Horizontal Scaling](#7-horizontal-scaling)
8. [Vertical Scaling](#8-vertical-scaling)
9. [Load Balancing](#9-load-balancing)
10. [Caching Strategy](#10-caching-strategy)
11. [Database Scaling](#11-database-scaling)
12. [Message Queue](#12-message-queue)
13. [Cost Optimization](#13-cost-optimization)
14. [SLA e Uptime](#14-sla-e-uptime)
15. [Glossário de Escalabilidade](#15-glossário-de-escalabilidade)

---

## 1. INTRODUÇÃO À ESCALABILIDADE

### 1.1 Objectivo da Escalabilidade

**Escalabilidade** é a capacidade do sistema crescer horizontalmente (mais máquinas) ou verticalmente (mais recursos) sem perder performance.

**Objectivo:** Planejar a escalabilidade desde o início, para que o sistema possa crescer de local (MVP) para cloud-native (produção) sem reescrever tudo.

### 1.2 Porquê Planejar Escalabilidade?

**Riscos sem Planejamento:**
- Sistema não escala quando necessário
- Refactoring caro para escalar
- Downtime durante migração
- Custo de reescrever componentes

**Benefícios com Planejamento:**
- Crescimento gradual (local → VPS → cloud)
- Componentes desacoplados (fáceis de escalar)
- Migração sem reescrever código
- Custo controlado (paga apenas o que precisa)

---

## 2. ARQUITECTURA DE ESCALA

### 2.1 Roadmap de Escala

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ROADMAP DE ESCALA (4 FASES)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: LOCAL (MVP)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Windows 11 PC                                                      │   │
│  │ SQLite database                                                    │   │
│  │ Task Scheduler                                                     │   │
│  │ APScheduler (single process)                                       │   │
│  │ Custo: €0/mês                                                      │   │
│  │ Capacidade: 1000 listings/dia                                     │   │
│  │ Uptime: ~80% (PC ligado 80% do tempo)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 2: VPS (PRODUÇÃO)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS (DigitalOcean, Hetzner, etc.)                                │   │
│  │ Ubuntu 22.04 LTS                                                   │   │
│  │ PostgreSQL database                                                │   │
│  │ Systemd (service)                                                 │   │
│  │ APScheduler (single process)                                       │   │
│  │ Custo: €20-30/mês                                                  │   │
│  │ Capacidade: 5000 listings/dia                                    │   │
│  │ Uptime: 99.5% (VPS uptime)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 3: CLOUD-NATIVE (DISTRIBUTED)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Kubernetes (K8s)                                                   │   │
│  │ PostgreSQL (RDS)                                                  │   │
│  │ Redis (ElastiCache)                                               │   │
│  │ Celery + RabbitMQ                                                 │   │
│  │ Prometheus + Grafana                                               │   │
│  │ Custo: €100-200/mês                                               │   │
│  │ Capacidade: 50000+ listings/dia                                  │   │
│  │ Uptime: 99.9% (HA)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FASE 4: MULTI-REGION (ENTERPRISE)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Multi-region deployment                                           │   │
│  │ CDN (CloudFront)                                                  │   │
│  │ Multi-master database                                             │   │
│  │ Global load balancer                                              │   │
│  │ Custo: €500-1000/mês                                              │   │
│  │ Capacidade: 500000+ listings/dia                                 │   │
│  │ Uptime: 99.99% (multi-region)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FASE 1: LOCAL (MVP)

### 3.1 Características

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FASE 1: LOCAL (MVP)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HARDWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Windows 11 PC                                                      │   │
│  │ CPU: 4+ cores                                                      │   │
│  │ RAM: 8GB+                                                          │   │
│  │ Disco: 100GB+ SSD                                                  │   │
│  │ Internet: Estável                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOFTWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Python 3.11+                                                       │   │
│  │ Virtual environment (venv)                                        │   │
│  │ SQLite database                                                    │   │
│  │ Task Scheduler                                                     │   │
│  │ APScheduler (AsyncIOScheduler)                                     │   │
│  │ Streamlit dashboard                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CAPACIDADE:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Scraping: 1000 listings/dia                                       │   │
│  │ ETL: 1000 listings/dia                                             │   │
│  │ Valuation: 1000 listings/dia                                      │   │
│  │ Scoring: 1000 listings/dia                                       │   │
│  │ Notification: 10-20/dia                                          │   │
│  │ Database: < 1GB (90 dias)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LIMITAÇÕES:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Single process (APScheduler)                                      │   │
│  │ SQLite (single writer)                                            │   │
│  │ PC precisa estar ligado 24/7                                     │   │
│  │ Sem alta disponibilidade                                            │   │
│  │ Sem backup automático na cloud                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTO: €0/mês                                                             │
│  UPTIME: ~80% (PC ligado 80% do tempo)                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. FASE 2: VPS (PRODUÇÃO)

### 4.1 Características

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FASE 2: VPS (PRODUÇÃO)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HARDWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS (DigitalOcean, Hetzner, etc.)                                │   │
│  │ CPU: 2-4 cores                                                     │   │
│  │ RAM: 4-8GB                                                         │   │
│  │ Disco: 80-160GB SSD                                               │   │
│  │ Internet: 1Gbps                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOFTWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Ubuntu 22.04 LTS                                                   │   │
│  │ Python 3.11+                                                       │   │
│  │ Virtual environment (venv)                                        │   │
│  │ PostgreSQL 14+                                                    │   │
│  │ Systemd (service)                                                 │   │
│  │ APScheduler (AsyncIOScheduler)                                     │   │
│  │ Streamlit dashboard                                               │   │
│  │ Nginx (reverse proxy)                                             │   │
│  │ Certbot (HTTPS)                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CAPACIDADE:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Scraping: 5000 listings/dia                                       │   │
│  │ ETL: 5000 listings/dia                                             │   │
│  │ Valuation: 5000 listings/dia                                      │   │
│  │ Scoring: 5000 listings/dia                                       │   │
│  │ Notification: 50-100/dia                                         │   │
│  │ Database: 10-20GB (90 dias)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VANTAGENS:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS uptime 99.5%                                                   │   │
│  │ PostgreSQL (multi-writers)                                         │   │
│  │ HTTPS (SSL/TLS)                                                    │   │
│  │ Backup automático (cron job)                                       │   │
│  │ Acesso remoto (SSH)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTO: €20-30/mês                                                         │
│  UPTIME: 99.5% (VPS uptime)                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Configuração Systemd

```ini
# /etc/systemd/system/realestate-engine.service
[Unit]
Description=Real Estate Opportunity Engine
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/realestate-engine
Environment="PATH=/home/ubuntu/realestate-engine/venv/bin"
ExecStart=/home/ubuntu/realestate-engine/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.3 Configuração Nginx

```nginx
# /etc/nginx/sites-available/realestate-engine
server {
    listen 80;
    server_name realestate.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTPS (com Certbot)
server {
    listen 443 ssl;
    server_name realestate.example.com;

    ssl_certificate /etc/letsencrypt/live/realestate.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/realestate.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 5. FASE 3: CLOUD-NATIVE (MICROSERVICES)

### 5.1 Características

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FASE 3: CLOUD-NATIVE (MICROSERVICES)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INFRAESTRUTURA:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Kubernetes (K8s)                                                   │   │
│  │ AWS / Azure / GCP                                                 │   │
│  │ Multi-zone deployment                                             │   │
│  │ Auto-scaling                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATABASES:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL (RDS / Azure Database / Cloud SQL)                    │   │
│  │ Redis (ElastiCache / Azure Cache / Memorystore)                   │   │
│  │ S3 / Azure Blob / Cloud Storage (backups, logs)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MESSAGE QUEUE:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ RabbitMQ (Amazon MQ / Azure Service Bus)                         │   │
│  │ Celery (task queue)                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MONITORING:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Prometheus (metrics)                                               │   │
│  │ Grafana (dashboard)                                                │   │
│  │ Loki (logs)                                                        │   │
│  │ Jaeger (tracing)                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MICROSERVICES:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Scraping Service (Nodriver)                                        │   │
│  │ ETL Service (Pipeline)                                             │   │
│  │ Valuation Service (ML models)                                     │   │
│  │ Scoring Service (Score calculators)                               │   │
│  │ Notification Service (Telegram)                                    │   │
│  │ Dashboard Service (Streamlit)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CAPACIDADE:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Scraping: 50000+ listings/dia                                      │   │
│  │ ETL: 50000+ listings/dia                                            │   │
│  │ Valuation: 50000+ listings/dia                                   │   │
│  │ Scoring: 50000+ listings/dia                                     │   │
│  │ Notification: 500-1000/dia                                        │   │
│  │ Database: 500GB+ (90 dias)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VANTAGENS:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Horizontal scaling (mais pods)                                     │   │
│  │ Auto-scaling (baseado em métricas)                                │   │
│  │ High availability (HA)                                             │   │
│  │ Multi-zone (failover automático)                                   │   │
│  │ Managed services (menos manutenção)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTO: €100-200/mês                                                       │
│  UPTIME: 99.9% (HA)                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. ESTRATÉGIA DE MIGRAÇÃO

### 6.1 Plano de Migração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PLANO DE MIGRAÇÃO (LOCAL → VPS)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SEMANA 1: PREPARAÇÃO                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Comprar VPS (DigitalOcean, Hetzner, etc.)                      │   │
│  │ - Configurar Ubuntu 22.04 LTS                                       │   │
│  │ - Instalar Python 3.11+                                             │   │
│  │ - Instalar PostgreSQL 14+                                           │   │
│  │ - Configurar firewall (ufw)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEMANA 2: DEPLOYMENT                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Clonar repositório no VPS                                         │   │
│  │ - Criar virtual environment                                         │   │
│  │ - Instalar dependencies                                            │   │
│  │ - Configurar .env                                                   │   │
│  │ - Configurar Systemd service                                       │   │
│  │ - Testar deployment manual                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEMANA 3: MIGRAÇÃO DE DADOS                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Exportar SQLite database                                         │   │
│  │ - Importar para PostgreSQL                                         │   │
│  │ - Verificar dados migrados                                          │   │
│  │ - Testar queries em PostgreSQL                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEMANA 4: CUTOVER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Parar scraping no local                                            │   │
│  │ - Iniciar scraping no VPS                                           │   │
│  │ - Configurar Nginx + HTTPS                                         │   │
│  │ - Configurar backup automático                                     │   │
│  │ - Monitorar durante 1 semana                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEMANA 5: MONITORING E OPTIMIZAÇÃO                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Configurar Prometheus + Grafana                                   │   │
│  │ - Configurar alertas                                               │   │
│  │ - Optimizar performance                                             │   │
│  │ - Configurar auto-scaling (se necessário)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. HORIZONTAL SCALING

### 7.1 Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              HORIZONTAL SCALING (FASE 3)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCRAPING SERVICE:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3 pods (Idealista, Imovirtual, Casa Sapo)                          │   │
│  │ Auto-scaling: 1-5 pods (baseado em CPU)                           │   │
│  │ Load balancer: Kubernetes Service                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ETL SERVICE:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2 pods (Normalizer, Deduplicator, Geocoder, Enricher, Validator)   │   │
│  │ Auto-scaling: 1-3 pods (baseado em queue length)                  │   │
│  │ Message queue: RabbitMQ                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VALUATION SERVICE:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2 pods (Hedonic Model, Comps Engine, INE, XGBoost)                │   │
│  │ Auto-scaling: 1-4 pods (baseado em CPU)                           │   │
│  │ Model cache: Redis                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCORING SERVICE:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2 pods (Score calculators, Red flags, Rationale)                  │   │
│  │ Auto-scaling: 1-3 pods (baseado em CPU)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NOTIFICATION SERVICE:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1 pod (Telegram bot)                                               │   │
│  │ Rate limiting: 5 notificações/dia por chat_id                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DASHBOARD SERVICE:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2 pods (Streamlit)                                                │   │
│  │ Load balancer: Kubernetes Ingress                                  │   │
│  │ Session affinity: Sticky (para manter estado)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. VERTICAL SCALING

### 8.1 Vertical Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              VERTICAL SCALING (FASE 2)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CPU: 2 → 4 cores                                                         │
│  RAM: 4GB → 8GB                                                           │
│  Disco: 80GB → 160GB SSD                                                 │
│                                                                             │
│  IMPACTO:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Scraping: 2x mais rápido                                             │   │
│  │ ETL: 1.5x mais rápido                                               │   │
│  │ Valuation: 1.5x mais rápido                                          │   │
│  │ Scoring: 2x mais rápido                                             │   │
│  │ Capacidade total: 2x                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTO: +50% (€20-30 → €30-45)                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. LOAD BALANCING

### 9.1 Load Balancing Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              LOAD BALANCING (KUBERNETES)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KUBERNETES SERVICE:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: ClusterIP (interno) ou LoadBalancer (externo)               │   │
│  │ Load balancing: Round-robin                                        │   │
│  │ Health checks: TCP / HTTP                                           │   │
│  │ Session affinity: None (stateless) ou ClientIP (stateful)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  KUBERNETES INGRESS:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Ingress (HTTP/HTTPS)                                          │   │
│  │ Load balancing: Round-robin                                        │   │
│  │ SSL/TLS: Cert-Manager (auto-renewal)                               │   │
│  │ Path-based routing: /dashboard → dashboard service                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. CACHING STRATEGY

### 10.1 Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CACHING STRATEGY (REDIS)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GEOCODE CACHE:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Key: geocode:{morada_hash}                                         │   │
│  │ Value: {lat, lon, freguesia, concelho}                             │   │
│  │ TTL: 365 dias (geocoding não muda)                                │   │
│  │ Hit rate: 80-90%                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INE DATA CACHE:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Key: ine:freguesia:{freguesia}:{ano}:{mes}                         │   │
│  │ Value: {preco_medio_m2, tendencia, volume}                         │   │
│  │ TTL: 30 dias (INE actualiza mensalmente)                           │   │
│  │ Hit rate: 95%                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MODEL CACHE:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Key: model:{model_name}:{version}                                  │   │
│  │ Value: {model_bytes, metadata}                                     │   │
│  │ TTL: 7 dias (modelos retrain a cada 30 dias)                        │   │
│  │ Hit rate: 90%                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VALUATION CACHE:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Key: valuation:{listing_id}:{timestamp_hash}                       │   │
│  │ Value: {valor_justo, discount, confianca}                          │   │
│  │ TTL: 24 horas (valuations mudam raramente)                         │   │
│  │ Hit rate: 70-80%                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCORE CACHE:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Key: score:{listing_id}:{timestamp_hash}                           │   │
│  │ Value: {score_total, classificacao, rationale}                     │   │
│  │ TTL: 24 horas (scores mudam raramente)                             │   │
│  │ Hit rate: 70-80%                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. DATABASE SCALING

### 11.1 Database Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DATABASE SCALING (POSTGRESQL)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 2 (VPS): SINGLE INSTANCE                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL 14+ (single instance)                                    │   │
│  │ Max connections: 100                                               │   │
│  │ Connection pooling: SQLAlchemy                                      │   │
│  │ WAL mode: On (performance)                                         │   │
│  │ Replication: None                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3 (CLOUD-NATIVE): READ REPLICAS                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL (RDS / Azure Database)                                  │   │
│  │ 1 primary (write)                                                  │   │
│  │ 2-3 read replicas (read)                                           │   │
│  │ Connection pooling: PgBouncer                                       │   │
│  │ WAL mode: On                                                       │   │
│  │ Replication: Streaming                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4 (ENTERPRISE): MULTI-MASTER                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL (RDS Multi-AZ)                                         │   │
│  │ 2-3 primary (write)                                                │   │
│  │ 3-5 read replicas (read)                                           │   │
│  │ Connection pooling: PgBouncer                                       │   │
│  │ WAL mode: On                                                       │   │
│  │ Replication: Multi-master (BDR)                                    │   │
│  │ Failover: Automatic (HA)                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. MESSAGE QUEUE

### 12.1 Message Queue Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MESSAGE QUEUE (RABBITMQ + CELERY)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QUEUES:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ scraping_queue: Raw listings → ETL                                │   │
│  │ etl_queue: Clean listings → Valuation                               │   │
│  │ valuation_queue: Clean + Valuations → Scoring                        │   │
│  │ scoring_queue: Clean + Valuations + Scores → Notification           │   │
│  │ notification_queue: Scores → Telegram                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WORKERS:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ scraping_worker: Processa scraping_queue                           │   │
│  │ etl_worker: Processa etl_queue                                      │   │
│  │ valuation_worker: Processa valuation_queue                          │   │
│  │ scoring_worker: Processa scoring_queue                              │   │
│  │ notification_worker: Processa notification_queue                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONFIGURAÇÃO CELERY:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Broker: RabbitMQ                                                    │   │
│  │ Backend: Redis                                                      │   │
│  │ Task soft time limit: 10 minutos                                    │   │
│  │ Task time limit: 30 minutos                                         │   │
│  │ Task max retries: 3                                                 │   │
│  │ Task default retry delay: 60 segundos                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. COST OPTIMIZATION

### 13.1 Cost Analysis por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              COST ANALYSIS POR FASE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: LOCAL (MVP)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS: €0                                                            │   │
│  │ Database: €0 (SQLite local)                                       │   │
│  │ Monitoring: €0 (logs locais)                                       │   │
│  │ Backup: €0 (backup local)                                         │   │
│  │ TOTAL: €0/mês                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS (PRODUÇÃO)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS: €20-30/mês (DigitalOcean 4GB RAM)                             │   │
│  │ Database: €0 (PostgreSQL no mesmo VPS)                             │   │
│  │ Monitoring: €0 (Prometheus + Grafana no mesmo VPS)                  │   │
│  │ Backup: €0 (S3 ou backup local)                                   │   │
│  │ TOTAL: €20-30/mês                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE (MICROSERVICES)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS: €80-120/mês (3-4 pods x €20-30)                               │   │
│  │ Database: €20-30/mês (RDS / Azure Database)                        │   │
│  │ Redis: €15-20/mês (ElastiCache / Azure Cache)                      │   │
│  │ RabbitMQ: €15-20/mês (Amazon MQ / Azure Service Bus)               │   │
│  │ Monitoring: €10-15/mês (Prometheus + Grafana managed)                │   │
│  │ Backup: €5-10/mês (S3 / Azure Blob)                                 │   │
│  │ TOTAL: €145-215/mês                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: MULTI-REGION (ENTERPRISE)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS: €400-600/mês (multi-region)                                   │   │
│  │ Database: €50-100/mês (multi-master RDS)                            │   │
│  │ Redis: €40-60/mês (multi-region ElastiCache)                       │   │
│  │ RabbitMQ: €40-60/mês (multi-region Amazon MQ)                      │   │
│  │ CDN: €20-30/mês (CloudFront / Azure CDN)                           │   │
│  │ Monitoring: €30-50/mês (Grafana Cloud / Azure Monitor)              │   │
│  │ Backup: €20-40/mês (multi-region S3)                               │   │
│  │ TOTAL: €600-940/mês                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. SLA E UPTIME

### 14.1 SLA por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SLA E UPTIME POR FASE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: LOCAL (MVP)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Uptime: ~80% (PC ligado 80% do tempo)                             │   │
│  │ Downtime: ~20% (PC desligado)                                        │   │
│  │ SLA: Sem SLA (MVP)                                                 │   │
│  │ Recovery: Manual (reiniciar PC)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS (PRODUÇÃO)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Uptime: 99.5% (VPS uptime)                                        │   │
│  │ Downtime: ~0.5% (manutenção, updates)                               │   │
│  │ SLA: 99% (acordado com utilizador)                                 │   │
│  │ Recovery: Automatic (Systemd auto-restart)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE (MICROSERVICES)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Uptime: 99.9% (HA)                                                │   │
│  │ Downtime: ~0.1% (failover automático)                              │   │
│  │ SLA: 99.9% (acordado com utilizador)                               │   │
│  │ Recovery: Automatic (Kubernetes auto-restart, failover)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: MULTI-REGION (ENTERPRISE)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Uptime: 99.99% (multi-region)                                     │   │
│  │ Downtime: ~0.01% (failover automático)                            │   │
│  │ SLA: 99.99% (acordado com utilizador)                              │   │
│  │ Recovery: Automatic (multi-region failover)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE ESCALABILIDADE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE ESCALABILIDADE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ESCALABILIDADE: Capacidade de crescer (horizontal ou vertical)        │
│                                                                             │
│  HORIZONTAL SCALING: Escala horizontal (mais máquinas)               │
│                                                                             │
│  VERTICAL SCALING: Escala vertical (mais recursos numa máquina)       │
│                                                                             │
│  MVP: Minimum Viable Product (produto mínimo viável)                  │
│                                                                             │
│  VPS: Virtual Private Server (servidor virtual)                       │
│                                                                             │
│  CLOUD-NATIVE: Cloud-native (arquitectura nativa da cloud)           │
│                                                                             │
│  MICROSERVICES: Microserviços (arquitectura de serviços pequenos)   │
│                                                                             │
│  KUBERNETES: Kubernetes (orquestrador de containers)                │
│                                                                             │
│  POD: Pod (unidade de execução no Kubernetes)                           │
│                                                                             │
│  SERVICE: Service (expose pods no Kubernetes)                           │
│                                                                             │
│  INGRESS: Ingress (HTTP/HTTPS load balancer no Kubernetes)            │
│                                                                             │
│  LOAD BALANCER: Load balancer (distribui tráfico)                     │
│                                                                             │
│  AUTO-SCALING: Auto-scaling (escala automaticamente)                │
│                                                                             │
│  HIGH AVAILABILITY: Alta disponibilidade (HA, 99.9% uptime)             │
│                                                                             │
│  FAILOVER: Failover (recuperação de falha)                            │
│                                                                             │
│  REDUNDANCY: Redundância (duplicação para HA)                          │
│                                                                             │
│  CACHING: Caching (armazenamento temporário para performance)         │
│                                                                             │
│  REDIS: Redis (cache em memória)                                      │
│                                                                             │
│  ELASTICACHE: ElastiCache (Redis gerenciado pela AWS)                │
│                                                                             │
│  MESSAGE QUEUE: Message queue (fila de mensagens)                     │
│                                                                             │
│  RABBITMQ: RabbitMQ (message broker)                                   │
│                                                                             │
│  CELERY: Celery (task queue para Python)                               │
│                                                                             │
│  WORKER: Worker (processa tasks da queue)                              │
│                                                                             │
│  CONNECTION POOLING: Connection pooling (pool de conexões)            │
│                                                                             │
│  READ REPLICA: Read replica (réplica de leitura)                      │
│                                                                             │
│  MULTI-MASTER: Multi-master (múltiplos primários para escrita)       │
│                                                                             │
│  STREAMING REPLICATION: Replicação streaming (em tempo real)         │
│                                                                             │
│  SLA: Service Level Agreement (acordo de nível de serviço)           │
│                                                                             │
│  UPTIME: Tempo de disponibilidade                                       │
│                                                                             │
│  DOWNTIME: Tempo de indisponibilidade                                    │
│                                                                             │
│  RECOVERY TIME: Tempo de recuperação (RTO)                              │
│                                                                             │
│  RECOVERY POINT OBJECTIVE: RPO (ponto de recuperação)                 │
│                                                                             │
│  COST OPTIMIZATION: Optimização de custos                             │
│                                                                             │
│  MULTI-REGION: Multi-region (deploy em múltiplas regiões)            │
│                                                                             │
│  CDN: Content Delivery Network (rede de distribuição de conteúdo)     │
│                                                                             │
│  PROMETHEUS: Prometheus (sistema de monitorização de métricas)      │
│                                                                             │
│  GRAFANA: Grafana (dashboard de visualização de métricas)            │
│                                                                             │
│  LOKI: Loki (centralização de logs)                                    │
│                                                                             │
│  JAEGER: Jaeger (distributed tracing)                                 │
│                                                                             │
│  SYSTEMD: Systemd (sistema de inicialização de serviços Linux)         │
│                                                                             │
│  NGINX: Nginx (web server e reverse proxy)                            │
│                                                                             │
│  SSL/TLS: SSL/TLS (encriptação de dados em trânsito)                   │
│                                                                             │
│  CERTBOT: Certbot (SSL certificates gratuitos)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 16 — Escalabilidade e Produção*
