# DEPLOYMENT LOCAL — REAL ESTATE OPPORTUNITY ENGINE
## Deployment Gratuito em Windows 11 com Task Scheduler

> **Este documento:** Especificação completa de deployment local  
> **Objectivo:** Fornecer especificação detalhada de deployment para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Deployment Local](#1-introducao-ao-deployment-local)
2. [Arquitectura de Deployment](#2-arquitetura-de-deployment)
3. [Requisitos de Sistema](#3-requisitos-de-sistema)
4. [Instalação de Dependências](#4-instalacao-de-dependencias)
5. [Configuração de Environment](#5-configuracao-de-environment)
6. [Execução Manual](#6-execucao-manual)
7. [Task Scheduler (Windows)](#7-task-scheduler-windows)
8. [Startup Script](#8-startup-script)
9. [Monitoramento Local](#9-monitoramento-local)
10. [Troubleshooting](#10-troubleshooting)
11. [Backup e Recovery](#11-backup-e-recovery)
12. [Performance Local](#12-performance-local)
13. [Escala: Local → Cloud](#13-escala-local-cloud)
14. [Best Practices Deployment](#14-best-practices-deployment)
15. [Glossário de Deployment](#15-glossário-de-deployment)

---

## 1. INTRODUÇÃO AO DEPLOYMENT LOCAL

### 1.1 Objectivo do Deployment Local

**Deployment Local** é a estratégia de executar o sistema inteiramente no PC do utilizador, sem custos de infraestrutura (VPS, cloud, etc.).

**Objectivo:** Executar o sistema gratuitamente no Windows 11, usando:
- Task Scheduler para agendamento
- SQLite para database (local)
- Local deployment (sem VPS)
- Custo zero (apenas electricidade)

### 1.2 Porquê Deployment Local?

**Vantagens:**
- Custo zero (sem VPS, sem cloud)
- GDPR compliance por design (dados ficam local)
- Simples de configurar
- Sem latência de rede
- Controlo total dos dados

**Desvantagens:**
- PC precisa estar ligado 24/7
- Sem alta disponibilidade (se PC cai, sistema para)
- Escalabilidade limitada (hardware do PC)
- Sem backup automático na cloud

---

## 2. ARQUITECTURA DE DEPLOYMENT

### 2.1 Arquitectura Local

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE DEPLOYMENT LOCAL (WINDOWS 11)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WINDOWS 11 PC                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - CPU: 4+ cores (recomendado 6+)                                    │   │
│  │ - RAM: 8GB+ (recomendado 16GB)                                       │   │
│  │ - Disco: 100GB+ SSD                                                  │   │
│  │ - Internet: Estável                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  PYTHON 3.11+                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Python 3.11                                                       │   │
│  │ - Virtual environment (venv)                                        │   │
│  │ - Dependencies (requirements.txt)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  APLICAÇÃO (main.py)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Scraping (Nodriver)                                              │   │
│  │ - ETL Pipeline                                                     │   │
│  │ - Valuation Engine                                                 │   │
│  │ - Scoring Engine                                                   │   │
│  │ - Notification Engine (Telegram)                                  │   │
│  │ - Dashboard Streamlit (http://localhost:8501)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  DATABASE (SQLite)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - realestate.db (data/db/)                                        │   │
│  │ - scheduler.db (data/db/)                                         │   │
│  │ - WAL mode para performance                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  TASK SCHEDULER (Windows)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Task "Real Estate Engine"                                       │   │
│  │ - Trigger: System startup + every 30 minutes                       │   │
│  │ - Action: python main.py                                          │   │
│  │ - Run as: User account                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  LOGS (Loguru)                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - logs/app_YYYY-MM-DD.log                                        │   │
│  │ - logs/errors_YYYY-MM-DD.log                                      │   │
│  │ - Rotation diária                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. REQUISITOS DE SISTEMA

### 3.1 Requisitos Mínimos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              REQUISITOS DE SISTEMA (WINDOWS 11)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HARDWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CPU: Intel Core i5 ou AMD Ryzen 5 (4+ cores)                        │   │
│  │ RAM: 8GB (recomendado 16GB)                                        │   │
│  │ Disco: 100GB SSD (recomendado 256GB SSD)                           │   │
│  │ GPU: Não necessário (CPU é suficiente)                              │   │
│  │ Internet: Estável (broadband, 10+ Mbps)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOFTWARE:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Windows 11 (64-bit)                                                 │   │
│  │ Python 3.11+ (64-bit)                                             │   │
│  │ Git (opcional, para versionamento)                                  │   │
│  │ Chrome ou Firefox (para dashboard)                                │   │
│  │ Telegram Desktop (opcional, para notificações)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RECURSOS:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CPU: 10-20% em idle, 50-80% durante scraping                     │   │
│  │ RAM: 2-4GB em idle, 6-8GB durante scraping                           │   │
│  │ Disco: 100MB para database, 1GB para logs (30 dias)                 │   │
│  │ Rede: 10-50 MB/dia (scraping de portais)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. INSTALAÇÃO DE DEPENDÊNCIAS

### 4.1 Instalar Python

```bash
# 1. Download Python 3.11+ de python.org
# https://www.python.org/downloads/

# 2. Instalar com:
# - Add Python to PATH ✓
# - Install for all users (opcional)

# 3. Verificar instalação
python --version
# Output: Python 3.11.x

# 4. Verificar pip
pip --version
# Output: pip 23.x.x
```

### 4.2 Criar Virtual Environment

```bash
# 1. Navegar para projecto
cd "d:\ia ultima"

# 2. Criar virtual environment
python -m venv venv

# 3. Activar virtual environment
# Windows PowerShell:
.\venv\Scripts\activate
# Windows CMD:
venv\Scripts\activate.bat

# 4. Verificar activação
# (prompt deve mostrar (venv))
```

### 4.3 Instalar Dependencies

```bash
# 1. Criar requirements.txt
# requirements.txt
streamlit==1.31.0
pandas==2.2.0
plotly==5.19.0
folium==0.16.0
streamlit-folium==0.18.0
sqlalchemy==2.0.25
loguru==0.7.2
python-dotenv==1.0.0
nodriver==0.31.0
apscheduler==3.10.4
python-telegram-bot==20.7
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
statsmodels==0.14.0
xgboost==2.0.2

# 2. Instalar dependencies
pip install -r requirements.txt

# 3. Verificar instalação
pip list
```

---

## 5. CONFIGURAÇÃO DE ENVIRONMENT

### 5.1 Criar .env

```bash
# Criar ficheiro .env na raiz do projecto
# d:\ia ultima\.env

# .env
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Database
DATABASE_URL=sqlite:///data/db/realestate.db
SCHEDULER_DATABASE_URL=sqlite:///data/db/scheduler.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Dashboard
DASHBOARD_HOST=localhost
DASHBOARD_PORT=8501

# Scraping
SCRAPING_FREQUENCY_MINUTES=30
```

### 5.2 Criar .env.example

```bash
# .env.example (para versionamento no git)
# Copiar para .env e preencher com valores reais

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

DATABASE_URL=sqlite:///data/db/realestate.db
SCHEDULER_DATABASE_URL=sqlite:///data/db/scheduler.db

LOG_LEVEL=INFO
LOG_DIR=logs

DASHBOARD_HOST=localhost
DASHBOARD_PORT=8501

SCRAPING_FREQUENCY_MINUTES=30
```

---

## 6. EXECUÇÃO MANUAL

### 6.1 Executar Aplicação

```bash
# 1. Activar virtual environment
.\venv\Scripts\activate

# 2. Navegar para projecto
cd "d:\ia ultima"

# 3. Executar aplicação principal
python main.py

# Output:
# [2026-01-15 10:30:00] INFO: Iniciando Real Estate Opportunity Engine
# [2026-01-15 10:30:01] INFO: Scraping iniciado
# [2026-01-15 10:45:00] INFO: Scraping completo (123 listings)
# [2026-01-15 10:45:01] INFO: ETL iniciado
# ...
```

### 6.2 Executar Dashboard

```bash
# 1. Activar virtual environment
.\venv\Scripts\activate

# 2. Navegar para projecto
cd "d:\ia ultima"

# 3. Executar dashboard
streamlit run dashboard/app.py

# Output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
```

### 6.3 Acessar Dashboard

```
# Abrir browser e aceder a:
http://localhost:8501

# O dashboard deve aparecer com:
# - Página Overview (KPIs, top listings, gráficos)
# - Página Search (filtros avançados)
# - Página Config (configurações)
# - Página System (status, logs)
```

---

## 7. TASK SCHEDULER (WINDOWS)

### 7.1 Configurar Task Scheduler

**Passo 1: Abrir Task Scheduler**
```
1. Press Windows + R
2. Escrever: taskschd.msc
3. Press Enter
```

**Passo 2: Criar Nova Task**
```
1. No painel direito, clicar "Create Basic Task"
2. Name: "Real Estate Engine"
3. Description: "Executa Real Estate Opportunity Engine automaticamente"
4. Clicar "Next"
```

**Passo 3: Configurar Trigger**
```
1. Select "When the computer starts"
2. Clicar "Next"
3. Select "Repeat task every: 30 minutes"
4. Clicar "Next"
```

**Passo 4: Configurar Action**
```
1. Select "Start a program"
2. Program/script: C:\Path\To\Python\python.exe
3. Add arguments: d:\ia ultima\main.py
4. Start in: d:\ia ultima
5. Clicar "Next"
```

**Passo 5: Configurar Settings**
```
1. Select "Open the Properties dialog"
2. Tab "General":
   - Select "Run whether user is logged on or not"
   - Select "Run with highest privileges"
3. Tab "Conditions":
   - Uncheck "Start the task only if the computer is on AC power"
4. Tab "Settings":
   - Select "Allow task to be run on demand"
   - Select "Run task as soon as possible after a scheduled start is missed"
5. Clicar "OK"
```

**Passo 6: Testar Task**
```
1. Na lista de tasks, clicar direito em "Real Estate Engine"
2. Select "Run"
3. Verificar logs para confirmar execução
```

---

## 8. STARTUP SCRIPT

### 8.1 Criar Startup Script

```batch
REM start.bat
REM Script de startup para Real Estate Opportunity Engine

@echo off
echo Iniciando Real Estate Opportunity Engine...

REM Activar virtual environment
call venv\Scripts\activate.bat

REM Executar aplicação
python main.py

REM Se aplicação cair, esperar 5 segundos e reiniciar
timeout /t 5 /nobreak >nul
goto :start
```

### 8.2 Configurar Startup Script no Task Scheduler

```
1. No Task Scheduler, editar a task "Real Estate Engine"
2. Tab "Actions"
3. Editar a action:
   - Program/script: C:\Windows\System32\cmd.exe
   - Add arguments: /c "d:\ia ultima\start.bat"
   - Start in: d:\ia ultima
4. Clicar "OK"
```

---

## 9. MONITORING LOCAL

### 9.1 Monitorar com Task Scheduler

```
1. Abrir Task Scheduler (taskschd.msc)
2. Navegar para "Task Scheduler Library"
3. Clicar em "Real Estate Engine"
4. Tab "History" para ver histórico de execuções
5. Tab "Triggers" para ver configuração
6. Tab "Actions" para ver acções
```

### 9.2 Monitorar com Dashboard

```
1. Aceder a http://localhost:8501
2. Navegar para "🖥️ System"
3. Ver:
   - Health checks status
   - Logs recentes
   - Métricas de performance
   - Status dos jobs
```

### 9.3 Monitorar com Logs

```
1. Navegar para logs/
2. Abrir app_YYYY-MM-DD.log
3. Verificar:
   - Erros (ERROR)
   - Avisos (WARNING)
   - Informações (INFO)
```

---

## 10. TROUBLESHOOTING

### 10.1 Problemas Comuns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PROBLEMAS COMUNS E SOLUÇÕES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEMA: Task Scheduler não executa task                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - Verificar se "Run whether user is logged on or not" está activado     │   │
│  - Verificar se "Run with highest privileges" está activado              │   │
│  - Verificar se path para Python está correcto                           │   │
│  - Verificar se path para main.py está correcto                           │   │
│  - Verificar History tab para ver erros                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROBLEMA: Scraping falha (DataDome, Cloudflare)                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - Verificar logs para ver erro específico                              │   │
│  - Se DataDome, considerar usar residential proxies (custo)             │   │
│  - Se Cloudflare, aumentar warm-up time                                │   │
│  - Se muitos erros, pausar scraping por 1 hora                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROBLEMA: Database locked                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - SQLite não suporta múltiplos writers                                │   │
│  - Verificar se há múltiplos processos a escrever                      │   │
│  - Activar WAL mode (já activado por default)                           │   │
│  - Se persistir, fechar todas as aplicações e reabrir                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROBLEMA: Dashboard não carrega                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - Verificar se Streamlit está a correr                                │   │
│  - Verificar se porta 8501 está disponível                              │   │
│  - Verificar firewall (pode bloquear localhost)                        │   │
│  - Parar Streamlit e reiniciar                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROBLEMA: Telegram notifications não enviadas                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - Verificar se TELEGRAM_BOT_TOKEN está correcto                       │   │
│  - Verificar se TELEGRAM_CHAT_ID está correcto                          │   │
│  - Verificar se bot está activo (enviar /start ao bot)                │   │
│  - Verificar logs para ver erro específico                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROBLEMA: PC lento durante scraping                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  SOLUÇÃO:                                                              │   │
│  - Scraping é intensivo em CPU                                         │   │
│  - Considerar reduzir frequência de scraping (ex: 60 minutos)          │   │
│  - Considerar reduzir número de portais (ex: só 4 principais)           │   │
│  - Considerar usar menos Nodriver spiders (usar curl-cffi para alguns)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. BACKUP E RECOVERY

### 11.1 Backup Automático

```python
# backup.py
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Backup da database."""
    db_path = Path("data/db/realestate.db")
    backup_dir = Path("data/backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"realestate_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    print(f"Backup criado em {backup_path}")

if __name__ == "__main__":
    backup_database()
```

### 11.2 Configurar Backup no Task Scheduler

```
1. Criar nova task: "Real Estate Engine Backup"
2. Trigger: Daily às 3:00 AM
3. Action: python backup.py
4. Settings: "Run whether user is logged on or not"
```

---

## 12. PERFORMANCE LOCAL

### 12.1 Métricas de Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MÉTRICAS DE PERFORMANCE LOCAL                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCRAPING:                                                                │
│  - Tempo: 10-15 minutos (17 portais)                                  │
│  - CPU: 50-80%                                                       │
│  - RAM: 2-4GB                                                        │
│  - Rede: 10-50 MB                                                     │
│                                                                             │
│  ETL:                                                                     │
│  - Tempo: 3-5 minutos (1000 listings)                                 │
│  - CPU: 20-40%                                                       │
│  - RAM: 1-2GB                                                        │
│  - Disco: Leitura/escrita 10-50 MB                                  │
│                                                                             │
│  VALUATION:                                                               │
│  - Tempo: 1-2 minutos (1000 listings)                                  │
│  - CPU: 30-50%                                                       │
│  - RAM: 1-2GB                                                        │
│                                                                             │
│  SCORING:                                                                 │
│  - Tempo: < 1 minuto (1000 listings)                                   │
│  - CPU: 20-40%                                                       │
│  - RAM: 500MB-1GB                                                    │
│                                                                             │
│  NOTIFICATION:                                                             │
│  - Tempo: < 10 segundos (5 notificações)                               │
│  - CPU: 5-10%                                                        │
│  - RAM: < 100MB                                                       │
│  - Rede: < 1 MB                                                       │
│                                                                             │
│  DASHBOARD:                                                               │
│  - Tempo carregamento página: < 2 segundos                              │
│  - CPU: 5-10% (idle), 20-30% (com gráficos)                            │
│  - RAM: 200-500MB                                                     │
│                                                                             │
│  TOTAL:                                                                    │
│  - Tempo total ciclo: 15-20 minutos                                    │
│  - CPU: 50-80% (pico durante scraping)                                │
│  - RAM: 4-6GB (pico)                                                  │
│  - Disco: < 100MB/dia (database + logs)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. ESCALA: LOCAL → CLOUD

### 13.1 Quando Migrar para Cloud?

**Sinais que precisa migrar:**
- PC não fica ligado 24/7
- Performance insuficiente
- Precisa de alta disponibilidade (HA)
- Precisa de acesso remoto (dashboard fora de casa)

### 13.2 Estratégia de Migração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         ESTRATÉGIA DE MIGRAÇÃO LOCAL → CLOUD                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1 (MVP): LOCAL                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Windows 11 PC                                                      │   │
│  │ SQLite database                                                    │   │
│  │ Task Scheduler                                                     │   │
│  │ Custo: €0/mês                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2 (PRODUÇÃO): VPS                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ VPS (DigitalOcean, Hetzner, etc.)                                │   │
│  │ Ubuntu 22.04 LTS                                                   │   │
│  │ PostgreSQL database                                                │   │
│  │ Systemd (service)                                                 │   │
│  │ Custo: €20-30/mês                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3 (CLOUD-NATIVE): MANAGED SERVICES                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AWS / Azure / GCP                                                 │   │
│  │ RDS / Azure Database / Cloud SQL (PostgreSQL)                     │   │
│  │ SQS / Azure Service Bus / PubSub (message queue)                 │   │
│  │ ElastiCache / Azure Cache / Memorystore (cache)                   │   │
│  │ Custo: €50-100/mês                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. BEST PRACTICES DEPLOYMENT

### 14.1 Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              BEST PRACTICES DEPLOYMENT LOCAL                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. VIRTUAL ENVIRONMENT                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Usar sempre virtual environment (venv)                             │   │
│  │ Não instalar dependencies globalmente                             │   │
│  │ Activar venv antes de executar comandos                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. ENVIRONMENT VARIABLES                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Usar .env para secrets (tokens, chat_ids)                          │   │
│  │ Nunca commit .env no git                                          │   │
│  │ Usar .env.example como template                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. TASK SCHEDULER                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Configurar "Run whether user is logged on or not"                   │   │
│  │ Configurar "Run with highest privileges"                            │   │
│  │ Verificar History tab para ver erros                                │   │
│  │ Testar task manualmente antes de agendar                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. BACKUP AUTOMÁTICO                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Backup diário da database                                          │   │
│  │ Backup semanal dos logs                                           │   │
│  │ Guardar backups por 30 dias                                       │   │
│  │ Testar restore periodicamente                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. MONITORING                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Verificar logs regularmente                                       │   │
│  │ Verificar Task Scheduler History                                   │   │
│  │ Verificar Dashboard (página System)                                │   │
│  │ Configurar alertas para falhas críticas                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. PERFORMANCE                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Monitorar CPU, RAM, disco                                         │   │
│  │ Se CPU > 90% por tempo prolongado, reduzir carga                   │   │
│  │ Se RAM > 90%, considerar upgrade de RAM                             │   │
│  │ Se disco > 80%, limpar logs antigos                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  7. SECURITY                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Manter Windows actualizado                                        │   │
│  │ Usar firewall                                                     │   │
│  │ Não expor portas desnecessárias                                   │   │
│  │ Usar antivirus                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  8. LOGS                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Configurar log rotation diária                                    │   │
│  │ Retenção de 30 dias                                               │   │
│  │ Comprimir logs antigos (zip)                                     │   │
│  │ Monitorar tamanho de logs                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE DEPLOYMENT

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE DEPLOYMENT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEPLOYMENT: Deployment (implementação do sistema)                       │
│                                                                             │
│  LOCAL DEPLOYMENT: Deployment local (no PC do utilizador)             │
│                                                                             │
│  CLOUD DEPLOYMENT: Deployment na cloud (VPS, managed services)         │
│                                                                             │
│  VPS: Virtual Private Server (servidor virtual na cloud)               │
│                                                                             │
│  TASK SCHEDULER: Agendador de tarefas do Windows                       │
│                                                                             │
│  VIRTUAL ENVIRONMENT: Ambiente virtual (isolado) de Python              │
│                                                                             │
│  VENV: Virtual environment (ambiente virtual Python)                   │
│                                                                             │
│  DEPENDENCIES: Dependências (bibliotecas Python)                        │
│                                                                             │
│  REQUIREMENTS.TXT: Ficheiro com lista de dependências                 │
│                                                                             │
│  .ENV: Ficheiro de variáveis de ambiente (secrets)                     │
│                                                                             │
│  .ENV.EXAMPLE: Template de .env (para versionamento)                    │
│                                                                             │
│  STARTUP SCRIPT: Script de inicialização (start.bat)                   │
│                                                                             │
│  SYSTEMD: System de inicialização de serviços Linux                     │
│                                                                             │
│  SERVICE: Serviço (processo em background)                              │
│                                                                             │
│  DAEMON: Daemon (processo em background)                                │
│                                                                             │
│  BACKUP: Backup (cópia de segurança)                                    │
│                                                                             │
│  RECOVERY: Recovery (restauração de backup)                             │
│                                                                             │
│  LOG ROTATION: Rotação de logs (arquivamento automático)               │
│                                                                             │
│  RETENTION: Retenção (tempo de guarda de logs/backups)                   │
│                                                                             │
│  MONITORING: Monitoramento (observabilidade do sistema)               │
│                                                                             │
│  HEALTH CHECK: Health check (verificação de saúde)                      │
│                                                                             │
│  PERFORMANCE: Performance (desempenho do sistema)                       │
│                                                                             │
│  CPU: Central Processing Unit (processador)                            │
│                                                                             │
│  RAM: Random Access Memory (memória)                                    │
│                                                                             │
│  SSD: Solid State Drive (disco sólido)                                 │
│                                                                             │
│  BROADBAND: Banda larga (internet de alta velocidade)                     │
│                                                                             │
│  HIGH AVAILABILITY: Alta disponibilidade (HA, 99.9% uptime)             │
│                                                                             │
│  UPTIME: Tempo de disponibilidade                                       │
│                                                                             │
│  DOWNTIME: Tempo de indisponibilidade                                    │
│                                                                             │
│  SCALABILITY: Escalabilidade (capacidade de crescimento)                │
│                                                                             │
│  MIGRATION: Migração (mover de local para cloud)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. SCRIPTS CROSS-PLATFORM (ONDA 2)

### 16.1 start.sh (macOS/Linux)

**Paridade com start.bat:**
- `start.sh` (macOS/Linux) com paridade total ao `start.bat` (Windows)
- 10 comandos: install, doctor, api, ui, dashboard, engine, all, test, help, menu
- Detecção robusta de venv
- Spawn de terminais para cada comando
- Mensagens consistentes entre plataformas

**Implementação:**
```bash
#!/bin/bash
# start.sh — Launcher cross-platform para macOS/Linux

# Detecta venv
if [ -d "venv312" ]; then
    VENV="venv312"
elif [ -d "venv" ]; then
    VENV="venv"
else
    echo "❌ Virtual environment não encontrado. Execute './start.sh install' primeiro."
    exit 1
fi

# Dispatch de comandos
case "$1" in
    install)
        python -m venv venv312
        source venv312/bin/activate
        pip install -r requirements.txt
        ;;
    doctor)
        source venv312/bin/activate
        python -m pytest tests/ -v
        ;;
    api)
        source venv312/bin/activate
        python -m realestate_engine.api.main &
        ;;
    ui)
        source venv312/bin/activate
        streamlit run realestate_engine/dashboard/app.py &
        ;;
    # ... outros comandos
esac
```

### 16.2 .gitignore Raiz Consolidado

**Propósito:** Excluir artefatos indesejados do versionamento

**Conteúdo:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv312/
venv/
.venv/

# Secrets
.env
*.key
*.pem
secrets/

# Logs
logs/
*.log
logs/**/*.log

# Data
data/db/*.db
data/cache/
data/backups/
*.sqlite
*.sqlite3

# Scripts debug
scripts/debug/_*.py
scripts/debug/_*.txt
scripts/debug/_*.log

# Terraform state
.terraform/
*.tfstate
*.tfstate.*

# LLM models
models/
*.bin
*.gguf
*.safetensors

# OS
.DS_Store
Thumbs.db
```

### 16.3 Benefícios

**Cross-Platform:**
- Utilizadores macOS/Linux podem usar o mesmo workflow que Windows
- Paridade funcional entre plataformas

**Git Clean:**
- .gitignore raiz consolida exclui artefatos sensíveis e temporários
- Repositório limpo, sem commits de dados sensíveis

**Consistência:**
- Scripts consistentes entre plataformas
- Mesmos comandos, mesma experiência

---

---

*Fim do Documento 14 — Deployment Local*
