# MONITORING E LOGGING — REAL ESTATE OPPORTUNITY ENGINE
## Observabilidade, Logs Estruturados e Health Checks

> **Este documento:** Especificação completa de monitoring e logging  
> **Objectivo:** Fornecer especificação detalhada de monitoring para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Monitoring](#1-introducao-ao-monitoring)
2. [Arquitectura de Monitoring](#2-arquitetura-de-monitoring)
3. [Logging com Loguru](#3-logging-com-loguru)
4. [Estrutura de Logs](#4-estrutura-de-logs)
5. [Health Checks](#5-health-checks)
6. [Métricas do Sistema](#6-metricas-do-sistema)
7. [Alertas](#7-alertas)
8. [Dashboard de Monitoring](#8-dashboard-de-monitoring)
9. [Log Rotation](#9-log-rotation)
10. [Error Tracking](#10-error-tracking)
11. [Performance Monitoring](#11-performance-monitoring)
12. [Distributed Tracing](#12-distributed-tracing)
13. [Escala: Local → Cloud](#13-escala-local-cloud)
14. [Best Practices Monitoring](#14-best-practices-monitoring)
15. [Glossário de Monitoring](#15-glossario-de-monitoring)

---

## 1. INTRODUÇÃO AO MONITORING

### 1.1 Objectivo do Monitoring

**Monitoring** é o conjunto de práticas para observar o estado do sistema em tempo real:
- Logs estruturados (Loguru)
- Health checks (HTTP endpoints)
- Métricas (tempo execução, taxa sucesso, throughput)
- Alertas (Telegram para falhas críticas)
- Dashboard (Streamlit para visualização)

**Objectivo:** Detectar problemas rapidamente, diagnosticar causas e garantir disponibilidade do sistema.

### 1.2 Porquê Monitoring?

**Problema sem Monitoring:**
- Falhas passam despercebidas
- Difícil diagnosticar problemas
- Sem visibilidade de performance
- Impossível garantir SLA

**Solução com Monitoring:**
- Logs estruturados para debugging
- Health checks para disponibilidade
- Métricas para performance
- Alertas para resposta rápida
- Dashboard para visibilidade

---

## 2. ARQUITECTURA DE MONITORING

### 2.1 Arquitectura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE MONITORING (MVP)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOGGING (Loguru)                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Logs estruturados (JSON)                                          │   │
│  │ - Múltiplos handlers (console + ficheiro)                           │   │
│  │ - Log rotation (diária)                                              │   │
│  │ - Retention (30 dias)                                                │   │
│  │ - Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  HEALTH CHECKS (FastAPI)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - /health (health check geral)                                     │   │
│  │ - /health/db (database health)                                      │   │
│  │ - /health/scheduler (scheduler health)                              │   │
│  │ - /health/scraping (scraping health)                                │   │
│  │ - /metrics (Prometheus metrics)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MÉTRICAS (Custom)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Scraping metrics (tempo, taxa sucesso, listings)                │   │
│  │ - ETL metrics (tempo, taxa erro, clean listings)                  │   │
│  │ - Valuation metrics (tempo, confiança, MAE)                       │   │
│  │ - Scoring metrics (tempo, distribuição scores)                    │   │
│  │ - Notification metrics (enviadas, falhas, success rate)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ALERTAS (Telegram)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Alertas CRITICAL (system down)                                  │   │
│  │ - Alertas ERROR (job failed)                                       │   │
│  │ - Alertas WARNING (performance degradation)                        │   │
│  │ - Alertas INFO (daily summary)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  DASHBOARD (Streamlit)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Página System (status, logs, métricas)                           │   │
│  │ - Gráficos de performance                                          │   │
│  │ - Logs recentes                                                     │   │
│  │ - Health checks status                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. LOGGING COM LOGURU

### 3.1 Configuração Loguru

```python
from loguru import logger
import sys
from pathlib import Path

# Remover handler default
logger.remove()

# Configurar console handler
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# Configurar ficheiro handler
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

logger.add(
    log_path / "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Rotação à meia-noite
    retention="30 days",  # Retenção 30 dias
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    compression="zip"  # Comprimir logs antigos
)

# Configurar ficheiro handler para erros
logger.add(
    log_path / "errors_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    compression="zip"
)
```

### 3.2 Uso de Loguru

```python
# INFO
logger.info("Scraping iniciado")

# WARNING
logger.warning("Listing sem preço, ignorando")

# ERROR
logger.error("Erro ao geocodificar listing: {error}", error=e)

# CRITICAL
logger.critical("Database connection failed, sistema parado")

# DEBUG
logger.debug("Fingerprint gerado: {fingerprint}", fingerprint=fp)
```

---

## 4. ESTRUTURA DE LOGS

### 4.1 Formato de Logs Estruturados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FORMATO DE LOGS ESTRUTURADOS (JSON)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  {                                                                         │
│    "timestamp": "2026-01-15T10:30:00",                                   │
│    "level": "INFO",                                                       │
│    "logger": "scraping.spider_manager",                                   │
│    "function": "run_all_spiders",                                        │
│    "line": 45,                                                             │
│    "message": "Scraping iniciado",                                       │
│    "context": {                                                            │
│      "spiders": 8,                                                         │
│      "portals": ["idealista", "imovirtual", "casa_sapo"]                 │
│    }                                                                      │
│  }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementação de Logs Estruturados

```python
from loguru import logger
import json

def log_structured(level: str, message: str, context: dict):
    """Log estruturado com contexto."""
    logger.bind(context=context).log(level, message)

# Exemplo de uso
log_structured(
    "INFO",
    "Scraping iniciado",
    {
        "spiders": 8,
        "portals": ["idealista", "imovirtual", "casa_sapo"]
    }
)

# Output:
# 2026-01-15 10:30:00 | INFO | scraping:spider_manager:run_all_spiders:45 | Scraping iniciado | context: {"spiders": 8, "portals": ["idealista", "imovirtual", "casa_sapo"]}
```

---

## 5. HEALTH CHECKS

### 5.1 Implementação Health Checks

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check geral."""
    checks = {
        'database': check_database(),
        'scheduler': check_scheduler(),
        'scraping': check_scraping()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    )

@app.get("/health/db")
async def health_check_database():
    """Health check da database."""
    healthy = check_database()
    
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            'status': 'healthy' if healthy else 'unhealthy',
            'check': 'database'
        }
    )

def check_database() -> bool:
    """Verifica se database está saudável."""
    try:
        # Tentar query simples
        from database.repository import DatabaseRepository
        repo = DatabaseRepository()
        repo.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Health check database falhou: {e}")
        return False

def check_scheduler() -> bool:
    """Verifica se scheduler está a correr."""
    try:
        from scheduler.orchestrator import SchedulerOrchestrator
        orchestrator = SchedulerOrchestrator()
        return orchestrator.scheduler.running
    except Exception as e:
        logger.error(f"Health check scheduler falhou: {e}")
        return False

def check_scraping() -> bool:
    """Verifica se scraping está a funcionar."""
    try:
        # Verificar se há scraping recente (últimos 2 horas)
        from database.repository import DatabaseRepository
        repo = DatabaseRepository()
        result = repo.execute("""
            SELECT COUNT(*) FROM raw_listings 
            WHERE scrape_timestamp > datetime('now', '-2 hours')
        """)
        
        # Se > 0 listings nas últimas 2 horas, scraping está a funcionar
        return result[0][0] > 0
    except Exception as e:
        logger.error(f"Health check scraping falhou: {e}")
        return False
```

---

## 6. MÉTRICAS DO SISTEMA

### 6.1 Métricas de Scraping

```python
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ScrapingMetrics:
    """Métricas de scraping."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.listings_scraped = 0
        self.portal_metrics = {}  # {portal: {success, failed, listings}}
    
    def start(self):
        """Inicia medição."""
        self.start_time = datetime.now()
    
    def end(self):
        """Termina medição."""
        self.end_time = datetime.now()
    
    def record_request(self, portal: str, success: bool, listings_count: int = 0):
        """Registra request."""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.listings_scraped += listings_count
        else:
            self.failed_requests += 1
        
        # Métricas por portal
        if portal not in self.portal_metrics:
            self.portal_metrics[portal] = {'success': 0, 'failed': 0, 'listings': 0}
        
        if success:
            self.portal_metrics[portal]['success'] += 1
            self.portal_metrics[portal]['listings'] += listings_count
        else:
            self.portal_metrics[portal]['failed'] += 1
    
    def get_summary(self) -> Dict:
        """Retorna resumo de métricas."""
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        throughput = (self.listings_scraped / duration) if duration > 0 else 0
        
        return {
            'duration_seconds': duration,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': success_rate,
            'listings_scraped': self.listings_scraped,
            'throughput_listings_per_second': throughput,
            'portal_metrics': self.portal_metrics
        }
```

### 6.2 Métricas de ETL

```python
class ETLMetrics:
    """Métricas de ETL."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.raw_count = 0
        self.normalized_count = 0
        self.duplicate_count = 0
        self.geocoded_count = 0
        self.enriched_count = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.errors = []
    
    def start(self):
        """Inicia medição."""
        self.start_time = datetime.now()
    
    def end(self):
        """Termina medição."""
        self.end_time = datetime.now()
    
    def record_error(self, component: str, error: str):
        """Registra erro."""
        self.errors.append({
            'component': component,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_summary(self) -> Dict:
        """Retorna resumo de métricas."""
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        throughput = (self.valid_count / duration) if duration > 0 else 0
        
        return {
            'duration_seconds': duration,
            'raw_count': self.raw_count,
            'normalized_count': self.normalized_count,
            'duplicate_count': self.duplicate_count,
            'geocoded_count': self.geocoded_count,
            'enriched_count': self.enriched_count,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'error_count': len(self.errors),
            'throughput_clean_listings_per_second': throughput
        }
```

---

## 7. ALERTAS

### 7.1 Sistema de Alertas

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AlertManager:
    """Gestor de alertas."""
    
    def __init__(self, telegram_bot):
        self.telegram_bot = telegram_bot
        self.alert_history = {}
    
    def send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        context: Dict = None
    ):
        """Envia alerta via Telegram."""
        # Verificar se alerta já foi enviado recentemente (evitar spam)
        alert_key = f"{severity}:{title}"
        
        if alert_key in self.alert_history:
            last_sent = self.alert_history[alert_key]
            time_since = (datetime.now() - last_sent).total_seconds()
            
            # Se alerta enviado há menos de 1 hora, não enviar novamente
            if time_since < 3600:
                logger.info(f"AlertManager: Alerta já enviado há {time_since}s, a saltar")
                return
        
        # Formatar mensagem
        emoji = {
            'CRITICAL': '🚨',
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }.get(severity, 'ℹ️')
        
        alert_message = f"""{emoji} *{severity}: {title}*

{message}

Context: {json.dumps(context, indent=2) if context else 'N/A'}
"""
        
        # Enviar via Telegram
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        try:
            await self.telegram_bot.send_message(chat_id, alert_message)
            self.alert_history[alert_key] = datetime.now()
            logger.info(f"AlertManager: Alerta enviado: {severity} - {title}")
        except Exception as e:
            logger.error(f"AlertManager: Erro ao enviar alerta: {e}")
    
    def send_daily_summary(self, metrics: Dict):
        """Envia resumo diário."""
        summary_message = f"""📊 *Resumo Diário - {datetime.now().strftime('%Y-%m-%d')}*

**Scraping:**
- Listings: {metrics.get('scraping_listings', 0)}
- Success Rate: {metrics.get('scraping_success_rate', 0):.1f}%

**ETL:**
- Clean Listings: {metrics.get('etl_clean_listings', 0)}
- Success Rate: {metrics.get('etl_success_rate', 0):.1f}%

**Valuation:**
- Valuations: {metrics.get('valuation_count', 0)}
- Avg Confidence: {metrics.get('valuation_avg_confidence', 0):.1f}%

**Scoring:**
- Scores: {metrics.get('scoring_count', 0)}
- Imperdíveis (≥8): {metrics.get('scoring_imperdiveis', 0)}

**Notifications:**
- Enviadas: {metrics.get('notification_sent', 0)}
- Success Rate: {metrics.get('notification_success_rate', 0):.1f}%
"""
        
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        await self.telegram_bot.send_message(chat_id, summary_message)
```

---

## 8. DASHBOARD DE MONITORING

### 8.1 Página System do Dashboard

```python
if page == "🖥️ System":
    st.header("🖥️ System Status")
    
    # Health Checks
    st.subheader("🔧 Health Checks")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_status = check_database()
        st.status("✅ Database" if db_status else "❌ Database")
    
    with col2:
        scheduler_status = check_scheduler()
        st.status("✅ Scheduler" if scheduler_status else "❌ Scheduler")
    
    with col3:
        scraping_status = check_scraping()
        st.status("✅ Scraping" if scraping_status else "❌ Scraping")
    
    with col4:
        # Health check geral
        all_healthy = db_status and scheduler_status and scraping_status
        st.status("✅ All Healthy" if all_healthy else "❌ Some Unhealthy")
    
    st.divider()
    
    # Logs Recentes
    st.subheader("📜 Logs Recentes")
    
    # Ler logs recentes
    log_file = "logs/app_2026-01-15.log"
    with open(log_file, 'r') as f:
        logs = f.readlines()[-20:]  # Últimas 20 linhas
    
    for log in logs:
        st.text(log)
    
    st.divider()
    
    # Métricas
    st.subheader("📊 Métricas do Sistema")
    
    # (Simulado - em produção viria das métricas reais)
    metrics = {
        'scraping_time': 12,
        'etl_time': 3,
        'valuation_time': 2,
        'scoring_time': 1,
        'total_time': 18
    }
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Scraping Time", f"{metrics['scraping_time']} min")
    
    with col2:
        st.metric("ETL Time", f"{metrics['etl_time']} min")
    
    with col3:
        st.metric("Valuation Time", f"{metrics['valuation_time']} min")
    
    with col4:
        st.metric("Scoring Time", f"{metrics['scoring_time']} min")
    
    with col5:
        st.metric("Total Time", f"{metrics['total_time']} min")
```

---

## 9. LOG ROTATION

### 9.1 Estratégia de Log Rotation

```python
from loguru import logger
from pathlib import Path

# Log rotation diária
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Rotação à meia-noite
    retention="30 days",  # Retenção 30 dias
    compression="zip"  # Comprimir logs antigos
)

# Log rotation por tamanho (alternativa)
logger.add(
    "logs/app.log",
    rotation="50 MB",  # Rotação quando ficheiro atingir 50MB
    retention="30 days",
    compression="zip"
)
```

---

## 10. ERROR TRACKING

### 10.1 Sistema de Error Tracking

```python
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Rastreio de erros."""
    
    def __init__(self):
        self.errors = []  # [{timestamp, type, message, context, count}]
    
    def track_error(self, error: Exception, context: Dict = None):
        """Rastreia erro."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Verificar se erro já existe (para agregar contagem)
        for error_entry in self.errors:
            if (error_entry['type'] == error_type and 
                error_entry['message'] == error_message):
                error_entry['count'] += 1
                error_entry['last_seen'] = datetime.now().isoformat()
                logger.error(f"ErrorTracker: Erro recorrente: {error_type} (count: {error_entry['count']})")
                return
        
        # Novo erro
        self.errors.append({
            'type': error_type,
            'message': error_message,
            'context': context,
            'count': 1,
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        })
        
        logger.error(f"ErrorTracker: Novo erro rastreado: {error_type}")
    
    def get_error_summary(self) -> Dict:
        """Retorna resumo de erros."""
        return {
            'total_errors': sum(e['count'] for e in self.errors),
            'unique_errors': len(self.errors),
            'top_errors': sorted(self.errors, key=lambda x: x['count'], reverse=True)[:10]
        }
```

---

## 11. PERFORMANCE MONITORING

### 11.1 Métricas de Performance

```python
import time
from typing import Dict, Callable
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance."""
    
    def __init__(self):
        self.metrics = {}  # {function_name: {total_time, count, avg_time, min_time, max_time}}
    
    def monitor(self, func: Callable) -> Callable:
        """Decorator para monitorar função."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                func_name = func.__name__
                
                if func_name not in self.metrics:
                    self.metrics[func_name] = {
                        'total_time': 0,
                        'count': 0,
                        'avg_time': 0,
                        'min_time': float('inf'),
                        'max_time': 0
                    }
                
                self.metrics[func_name]['total_time'] += duration
                self.metrics[func_name]['count'] += 1
                self.metrics[func_name]['avg_time'] = (
                    self.metrics[func_name]['total_time'] / self.metrics[func_name]['count']
                )
                self.metrics[func_name]['min_time'] = min(
                    self.metrics[func_name]['min_time'],
                    duration
                )
                self.metrics[func_name]['max_time'] = max(
                    self.metrics[func_name]['max_time'],
                    duration
                )
                
                logger.debug(
                    f"PerformanceMonitor: {func_name} levou {duration:.3f}s "
                    f"(avg: {self.metrics[func_name]['avg_time']:.3f}s)"
                )
            
            return result
        
        return wrapper
    
    def get_summary(self) -> Dict:
        """Retorna resumo de performance."""
        return self.metrics
```

---

## 12. DISTRIBUTED TRACING

### 12.1 Quando Implementar?

**Sinais que precisa de Distributed Tracing:**
- Sistema distribuído (múltiplos serviços)
- Difícil rastrear requisições através de componentes
- Problemas de performance não identificados com logs simples

**Fase 3 (Microservices):**
- Implementar OpenTelemetry
- Exportar para Jaeger ou Grafana Tempo
- Visualizar traces em dashboard

---

## 13. ESCALA: LOCAL → CLOUD

### 13.1 Estratégia de Escala de Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         ESTRATÉGIA DE ESCALA DE MONITORING                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1 (MVP): LOCAL                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Loguru (ficheiros locais)                                          │   │
│  │ - Health checks (FastAPI local)                                      │   │
│  │ - Métricas custom (em memória)                                      │   │
│  │ - Alertas Telegram                                                  │   │
│  │ - Dashboard Streamlit                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2 (PRODUÇÃO): CLOUD                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Loguru + Loki (centralização de logs)                            │   │
│  │ - Health checks (Kubernetes liveness/readiness probes)              │   │
│  │ - Prometheus + Grafana (métricas)                                   │   │
│  │ - AlertManager (alertas)                                           │   │
│  │ - Dashboard Grafana                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3 (MICROSERVICES): DISTRIBUTED TRACING                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - OpenTelemetry (instrumentação)                                  │   │
│  │ - Jaeger ou Grafana Tempo (tracing)                               │   │
│  │ - Distributed tracing (end-to-end)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. BEST PRACTICES MONITORING

### 14.1 Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              BEST PRACTICES MONITORING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LOGS ESTRUTURADOS                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Use formato JSON estruturado                                       │   │
│  │ Inclua contexto (timestamp, level, logger, function, line)         │   │
│  │ Use níveis apropriados (DEBUG, INFO, WARNING, ERROR, CRITICAL)     │   │
│  │ Não logue dados pessoais (GDPR)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. LOG ROTATION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rotação diária ou por tamanho                                       │   │
│  │ Retenção 30-90 dias                                                │   │
│  │ Compressão de logs antigos (zip)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. HEALTH CHECKS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Implemente health checks para todos os componentes                 │   │
│  │ Database, scheduler, scraping, etc.                               │   │
│  │ Exponha via HTTP endpoint (/health)                                │   │
│  │ Kubernetes liveness/readiness probes (produção)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. MÉTRICAS RELEVANTES                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Métricas de performance (tempo execução, throughput)               │   │
│  │ Métricas de negócio (listings, scores, notificações)               │   │
│  │ Métricas de erro (taxa erro, tipos de erro)                       │   │
│  │ Métricas de recursos (CPU, memória, disco)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. ALERTAS APROPRIADOS                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CRITICAL: System down, database connection failed                 │   │
│  │ ERROR: Job failed, scraping failed                                 │   │
│  │ WARNING: Performance degradation, high error rate                  │   │
│  │ INFO: Daily summary                                               │   │
│  │ Evite spam (rate limiting de alertas)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. DASHBOARD VISÍVEL                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Dashboard com status, logs, métricas                              │   │
│  │ Gráficos de performance                                          │   │
│  │ Atualização em tempo real ou periódica                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE MONITORING

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE MONITORING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MONITORING: Observabilidade do sistema (logs, métricas, alertas)      │
│                                                                             │
│  LOGGING: Registo de eventos e erros                                     │
│                                                                             │
│  LOGURU: Biblioteca Python para logging estruturado                   │
│                                                                             │
│  LOG ESTRUTURADO: Log com formato JSON e contexto                      │
│                                                                             │
│  LOG LEVEL: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)       │
│                                                                             │
│  LOG ROTATION: Rotação de logs (diária, por tamanho)                  │
│                                                                             │
│  LOG RETENTION: Retenção de logs (30-90 dias)                            │
│                                                                             │
│  HEALTH CHECK: Verificação de saúde do sistema                         │
│                                                                             │
│  LIVENESS PROBE: Probe de liveness (Kubernetes)                        │
│                                                                             │
│  READINESS PROBE: Probe de readiness (Kubernetes)                      │
│                                                                             │
│  MÉTRICA: Medida de performance ou comportamento                       │
│                                                                             │
│  PROMETHEUS: Sistema de monitorização de métricas                      │
│                                                                             │
│  GRAFANA: Dashboard para visualização de métricas                      │
│                                                                             │
│  ALERT: Alerta (notificação de problema)                               │
│                                                                             │
│  ALERTMANAGER: Gestor de alertas (Prometheus)                           │
│                                                                             │
│  ERROR TRACKING: Rastreio de erros (tipos, contagem, contexto)       │
│                                                                             │
│  PERFORMANCE MONITORING: Monitoramento de performance               │
│                                                                             │
│  THROUGHPUT: Volume de dados processados por segundo                   │
│                                                                             │
│  LATENCY: Tempo de resposta                                              │
│                                                                             │
│  ERROR RATE: Taxa de erro (erros / total requests)                     │
│                                                                             │
│  SUCCESS RATE: Taxa de sucesso (sucesso / total requests)              │
│                                                                             │
│  DISTRIBUTED TRACING: Rastreio distribuído (end-to-end)              │
│                                                                             │
│  OPENTELEMETRY: Framework de instrumentação para tracing             │
│                                                                             │
│  JAEGER: Sistema de distributed tracing                                │
│                                                                             │
│  GRAFANA TEMPO: Sistema de distributed tracing (Grafana)               │
│                                                                             │
│  LOKI: Sistema de centralização de logs (Grafana)                     │
│                                                                             │
│  OBSERVABILITY: Capacidade de observar estado interno do sistema       │
│                                                                             │
│  SLA: Service Level Agreement (acordo de nível de serviço)           │
│                                                                             │
│  UPTIME: Tempo de disponibilidade                                       │
│                                                                             │
│  DOWNTIME: Tempo de indisponibilidade                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 12 — Monitoring e Logging*
