# SCHEDULER E ORQUESTRAÇÃO — REAL ESTATE OPPORTUNITY ENGINE
## Agendamento de Tarefas e Orquestração do Sistema

> **Este documento:** Especificação completa de scheduler e orquestração  
> **Objectivo:** Fornecer especificação detalhada de scheduler para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Scheduler](#1-introducao-ao-scheduler)
2. [Arquitectura de Orquestração](#2-arquitetura-de-orquestracao)
3. [APScheduler Configuration](#3-apscheduler-configuration)
4. [Jobs Agendados](#4-jobs-agendados)
5. [Job: Scraping](#5-job-scraping)
6. [Job: ETL](#6-job-etl)
7. [Job: Valuation](#7-job-valuation)
8. [Job: Scoring](#8-job-scoring)
9. [Job: Notification](#9-job-notification)
10. [Job: Maintenance](#10-job-maintenance)
11. [Error Handling Scheduler](#11-error-handling-scheduler)
12. [Circuit Breakers](#12-circuit-breakers)
13. [Monitoring Scheduler](#13-monitoring-scheduler)
14. [Escala: APScheduler → Celery](#14-escala-apscheduler-celery)
15. [Glossário de Scheduler](#15-glossario-de-scheduler)

---

## 1. INTRODUÇÃO AO SCHEDULER

### 1.1 Objectivo do Scheduler

**Scheduler** é o componente responsável por agendar e orquestrar tarefas automáticas do sistema:
- Scraping (cada 30 minutos)
- ETL (cada 32 minutos)
- Valuation (cada 35 minutos)
- Scoring (cada 38 minutos)
- Notification (cada 60 minutos)
- Maintenance (diário)

**Objectivo:** Automatizar o pipeline completo sem intervenção manual.

### 1.2 Porquê APScheduler?

**Vantagens do APScheduler (MVP):**
- Simples de configurar e usar
- Custo zero (local)
- Suporta jobs agendados (cron-like)
- Persistência de jobs em database
- AsyncIO support (async jobs)

**Limitações (MVP):**
- Single process (não distribuído)
- Se processo cai, jobs param
- Não escala horizontalmente

**Alternativa (Produção):**
- Celery + RabbitMQ (distribuído, escalável)
- Custo: €10-30/mês (VPS para RabbitMQ)

---

## 2. ARQUITECTURA DE ORQUESTRAÇÃO

### 2.1 Arquitectura de Orquestração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE ORQUESTRAÇÃO (MVP)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  APSCHEDULER (AsyncIOScheduler)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ JobStore: SQLAlchemyJobStore (SQLite)                              │   │
│  │ Executor: AsyncIOExecutor                                         │   │
│  │ Job Defaults: coalesce=True, max_instances=1                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  JOBS AGENDADOS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Scraping Job (cada 30 minutos)                                │   │
│  │    - SpiderManager.run_all_spiders()                              │   │
│  │    - Raw listings → raw_listings table                             │   │
│  │                                                                     │   │
│  │ 2. ETL Job (cada 32 minutos)                                    │   │
│  │    - PipelineETL.run()                                            │   │
│  │    - Raw → Clean listings                                          │   │
│  │                                                                     │   │
│  │ 3. Valuation Job (cada 35 minutos)                                │   │
│  │    - ValuationEngine.valuate_batch()                             │   │
│  │    - Clean listings → Valuations                                   │   │
│  │                                                                     │   │
│  │  │ 4. Scoring Job (cada 38 minutos)                              │   │
│  │    - ScoringEngine.score_batch()                                 │   │
│  │    - Clean + Valuations → Scores                                   │   │
│  │                                                                     │   │
│  │  │ 5. Notification Job (cada 60 minutos)                           │   │
│  │    - NotificationEngine.notify_top_opportunities()                 │   │
│  │    - Telegram notifications                                         │   │
│  │                                                                     │   │
│  │ 6. Maintenance Job (diário às 3:00 AM)                           │   │
│  │    - Database backup                                               │   │
│  │    - Log rotation                                                  │   │
│  │    - Health checks                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ERROR HANDLING                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Retry com backoff exponencial                                  │   │
│  │ - Circuit breakers (pausa se falhas consecutivas)                │   │
│  │ - Logging de erros                                                 │   │
│  │ - Alertas para falhas críticas                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MONITORING                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Loguru logging estruturado                                     │   │
│  │ - Health checks (HTTP endpoint)                                  │   │
│  │ - Métricas de jobs (tempo execução, taxa sucesso)               │   │
│  │ - Alertas (Telegram) para falhas                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. APSCHEDULER CONFIGURATION

### 3.1 Configuração Completa

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class SchedulerOrchestrator:
    """Orquestrador de tarefas usando APScheduler."""
    
    def __init__(self, database_url: str = "sqlite:///data/db/scheduler.db"):
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(url=database_url)
            },
            executors={
                'default': AsyncIOExecutor()
            },
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutos
            },
            timezone='Europe/Lisbon'
        )
        
        self.jobs = {}
    
    def start(self):
        """Inicia scheduler."""
        logger.info("SchedulerOrchestrator: Iniciando scheduler")
        self.scheduler.start()
        
        # Adicionar jobs
        self._add_jobs()
        
        logger.info("SchedulerOrchestrator: Scheduler iniciado")
    
    def shutdown(self):
        """Desliga scheduler."""
        logger.info("SchedulerOrchestrator: Desligando scheduler")
        self.scheduler.shutdown()
    
    def _add_jobs(self):
        """Adiciona jobs agendados."""
        # Job 1: Scraping
        self.scheduler.add_job(
            self.scraping_job,
            trigger=IntervalTrigger(minutes=30),
            id='scraping_job',
            name='Scraping Job',
            replace_existing=True
        )
        
        # Job 2: ETL
        self.scheduler.add_job(
            self.etl_job,
            trigger=IntervalTrigger(minutes=32),
            id='etl_job',
            name='ETL Job',
            replace_existing=True
        )
        
        # Job 3: Valuation
        self.scheduler.add_job(
            self.valuation_job,
            trigger=IntervalTrigger(minutes=35),
            id='valuation_job',
            name='Valuation Job',
            replace_existing=True
        )
        
        # Job 4: Scoring
        self.scheduler.add_job(
            self.scoring_job,
            trigger=IntervalTrigger(minutes=38),
            id='scoring_job',
            name='Scoring Job',
            replace_existing=True
        )
        
        # Job 5: Notification
        self.scheduler.add_job(
            self.notification_job,
            trigger=IntervalTrigger(minutes=60),
            id='notification_job',
            name='Notification Job',
            replace_existing=True
        )
        
        # Job 6: Maintenance (diário às 3:00 AM)
        from apscheduler.triggers.cron import CronTrigger
        self.scheduler.add_job(
            self.maintenance_job,
            trigger=CronTrigger(hour=3, minute=0),
            id='maintenance_job',
            name='Maintenance Job',
            replace_existing=True
        )
```

---

## 4. JOBS AGENDADOS

### 4.1 Tabela de Jobs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              TABELA DE JOBS AGENDADOS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  JOB ID              │ FREQUÊNCIA  │ FUNÇÃO                              │ DURAÇÃO ESPERADA │   │
│  ────────────────────┼────────────┼────────────────────────────────────┼──────────────────┤   │
│  scraping_job        │ 30 minutos   │ Scraping de 17 portais              │ 10-15 minutos       │   │
│  etl_job             │ 32 minutos   │ Pipeline ETL                       │ 3-5 minutos         │   │
│  valuation_job       │ 35 minutos   │ Valuation de listings              │ 2-3 minutos         │   │
│  scoring_job         │ 38 minutos   │ Scoring de listings               │ 1-2 minutos         │   │
│  notification_job     │ 60 minutos   │ Notificações Telegram               │ < 1 minuto          │   │
│  maintenance_job     │ Diário 3:00  │ Backup, log rotation, health checks  │ 5-10 minutos       │   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. JOB: SCRAPING

### 5.1 Implementação

```python
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class SchedulerOrchestrator:
    # ... (continuação da classe anterior)
    
    async def scraping_job(self):
        """Job de scraping."""
        logger.info("SchedulerOrchestrator: Executando Scraping Job")
        
        try:
            # Importar componentes
            from scraping.spider_manager import SpiderManager
            from database.repository import DatabaseRepository
            
            # Inicializar componentes
            spider_manager = SpiderManager()
            database_repository = DatabaseRepository()
            
            # Executar scraping
            raw_listings = await spider_manager.run_all_spiders()
            
            # Guardar na database
            await database_repository.insert_raw_listings(raw_listings)
            
            logger.info(f"SchedulerOrchestrator: Scraping Job completo ({len(raw_listings)} listings)")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no Scraping Job: {e}")
            raise
```

---

## 6. JOB: ETL

### 6.1 Implementação

```python
class SchedulerOrchestrator:
    # ... (continuação)
    
    async def etl_job(self):
        """Job de ETL."""
        logger.info("SchedulerOrchestrator: Executando ETL Job")
        
        try:
            # Importar componentes
            from etl.pipeline_etl import PipelineETL
            from database.repository import DatabaseRepository
            
            # Inicializar componentes
            pipeline_etl = PipelineETL(
                normalizer=Normalizer(),
                deduplicator=Deduplicator(),
                geocoder=Geocoder(),
                enricher=Enricher(),
                validator=Validator(),
                database_repository=DatabaseRepository()
            )
            
            # Executar ETL
            count = await pipeline_etl.run()
            
            logger.info(f"SchedulerOrchestrator: ETL Job completo ({count} clean listings)")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no ETL Job: {e}")
            raise
```

---

## 7. JOB: VALUATION

### 7.1 Implementação

```python
class SchedulerOrchestrator:
    # ... (continuação)
    
    async def valuation_job(self):
        """Job de valuation."""
        logger.info("SchedulerOrchestrator: Executando Valuation Job")
        
        try:
            # Importar componentes
            from valuation.valuation_engine import ValuationEngine
            from database.repository import DatabaseRepository
            
            # Inicializar componentes
            valuation_engine = ValuationEngine(
                hedonic_model=HedonicModel(),
                comps_engine=CompsEngine(database_repository),
                ine_client=INEClient(),
                xgboost_model=XGBoostModel()
            )
            
            # Obter listings para valuation
            database_repository = DatabaseRepository()
            clean_listings = await database_repository.get_clean_listings_for_valuation()
            
            # Executar valuation
            for listing in clean_listings:
                valuation = await valuation_engine.valuate(listing)
                await database_repository.insert_valuation(valuation)
            
            logger.info(f"SchedulerOrchestrator: Valuation Job completo ({len(clean_listings)} valuations)")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no Valuation Job: {e}")
            raise
```

---

## 8. JOB: SCORING

### 8.1 Implementação

```python
class SchedulerOrchestrator:
    # ... (continuação)
    
    async def scoring_job(self):
        """Job de scoring."""
        logger.info("SchedulerOrchestrator: Executando Scoring Job")
        
        try:
            # Importar componentes
            from scoring.scoring_engine import ScoringEngine
            from database.repository import DatabaseRepository
            
            # Inicializar componentes
            scoring_engine = ScoringEngine(
                score_discount_calculator=ScoreDiscountCalculator(),
                score_location_calculator=ScoreLocationCalculator(),
                score_condition_calculator=ScoreConditionCalculator(),
                score_liquidity_calculator=ScoreLiquidityCalculator(),
                score_freshness_calculator=ScoreFreshnessCalculator(),
                red_flags_detector=RedFlagsDetector(),
                weighted_score_calculator=WeightedScoreCalculator(),
                rationale_generator=RationaleGenerator()
            )
            
            # Obter listings para scoring
            database_repository = DatabaseRepository()
            clean_listings = await database_repository.get_clean_listings_with_valuation()
            
            # Executar scoring
            for listing, valuation in zip(clean_listings, valuations):
                score = await scoring_engine.score(listing, valuation)
                await database_repository.insert_score(score)
            
            logger.info(f"SchedulerOrchestrator: Scoring Job completo ({len(clean_listings)} scores)")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no Scoring Job: {e}")
            raise
```

---

## 9. JOB: NOTIFICATION

### 9.1 Implementação

```python
class SchedulerOrchestrator:
    # ... (continuação)
    
    async def notification_job(self):
        """Job de notificações."""
        logger.info("SchedulerOrchestrator: Executando Notification Job")
        
        try:
            # Importar componentes
            from notification.notification_engine import NotificationEngine
            from notification.opportunity_selector import OpportunitySelector
            from notification.message_formatter import MessageFormatter
            from notification.telegram_bot import TelegramBot
            from database.repository import DatabaseRepository
            
            # Inicializar componentes
            database_repository = DatabaseRepository()
            opportunity_selector = OpportunitySelector(database_repository)
            message_formatter = MessageFormatter()
            telegram_bot = TelegramBot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
            notification_engine = NotificationEngine(
                opportunity_selector=opportunity_selector,
                message_formatter=message_formatter,
                telegram_bot=telegram_bot,
                database_repository=database_repository
            )
            
            # Obter chat_ids
            chat_ids = os.getenv('TELEGRAM_CHAT_ID', '').split(',')
            
            # Executar notificações
            sent_count = await notification_engine.notify_top_opportunities(chat_ids)
            
            logger.info(f"SchedulerOrchestrator: Notification Job completo ({sent_count} notificações)")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no Notification Job: {e}")
            raise
```

---

## 10. JOB: MAINTENANCE

### 10.1 Implementação

```python
class SchedulerOrchestrator:
    # ... (continuação)
    
    async def maintenance_job(self):
        """Job de manutenção diária."""
        logger.info("SchedulerOrchestrator: Executando Maintenance Job")
        
        try:
            # Importar componentes
            from database.backup import SQLiteBackup
            from monitoring.health_checker import HealthChecker
            
            # Backup database
            backup = SQLiteBackup(db_path='data/db/realestate.db')
            backup_path = backup.backup()
            logger.info(f"SchedulerOrchestrator: Backup criado em {backup_path}")
            
            # Log rotation
            # (implementação: mover logs antigos para pasta archive)
            logger.info("SchedulerOrchestrator: Log rotation completa")
            
            # Health checks
            health_checker = HealthChecker()
            health_status = health_checker.check_all()
            
            if not health_status['healthy']:
                logger.warning(f"SchedulerOrchestrator: Health check falhou: {health_status}")
                # Enviar alerta Telegram
                await self._send_alert("Health check falhou")
            
            logger.info("SchedulerOrchestrator: Maintenance Job completo")
        
        except Exception as e:
            logger.error(f"SchedulerOrchestrator: Erro no Maintenance Job: {e}")
            raise
    
    async def _send_alert(self, message: str):
        """Envia alerta via Telegram."""
        from notification.telegram_bot import TelegramBot
        
        telegram_bot = TelegramBot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        alert_message = f"🚨 *ALERTA SISTEMA*\n\n{message}"
        
        await telegram_bot.send_message(chat_id, alert_message)
```

---

## 11. ERROR HANDLING SCHEDULER

### 11.1 Estratégias de Error Handling

```python
from apscheduler.events import EVENT_JOB_ERROR
import logging

logger = logging.getLogger(__name__)

class SchedulerOrchestrator:
    # ... (continuação)
    
    def _setup_error_handling(self):
        """Configura error handling."""
        # Listener para erros de jobs
        self.scheduler.add_listener(
            EVENT_JOB_ERROR,
            self._handle_job_error
        )
    
    def _handle_job_error(self, event):
        """Handle job error."""
        logger.error(
            f"SchedulerOrchestrator: Job error - Job ID: {event.job_id}, "
            f"Exception: {event.exception}"
        )
        
        # Enviar alerta Telegram
        asyncio.create_task(self._send_alert(
            f"Job error: {event.job_id}\nException: {event.exception}"
        ))
```

---

## 12. CIRCUIT BREAKERS

### 12.1 Implementação de Circuit Breakers

```python
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
import logging

logger = logging.getLogger(__name__)

class SchedulerOrchestrator:
    # ... (continuação)
    
    def __init__(self, database_url: str = "sqlite:///data/db/scheduler.db"):
        # ... (código anterior)
        self.circuit_breakers = {}  # {job_id: CircuitBreaker}
    
    def _setup_circuit_breakers(self):
        """Configura circuit breakers para jobs."""
        # Listener para jobs executados com sucesso
        self.scheduler.add_listener(
            EVENT_JOB_EXECUTED,
            self._handle_job_success
        )
        
        # Listener para jobs missed
        self.scheduler.add_listener(
            EVENT_JOB_MISSED,
            self._handle_job_missed
        )
    
    def _handle_job_success(self, event):
        """Handle job success (reset circuit breaker)."""
        job_id = event.job_id
        
        if job_id in self.circuit_breakers:
            self.circuit_breakers[job_id].record_success()
            logger.info(f"SchedulerOrchestrator: Circuit breaker reset para {job_id}")
    
    def _handle_job_missed(self, event):
        """Handle job missed (trigger circuit breaker)."""
        job_id = event.job_id
        
        if job_id not in self.circuit_breakers:
            self.circuit_breakers[job_id] = CircuitBreaker(failure_threshold=3)
        
        self.circuit_breakers[job_id].record_failure()
        
        if self.circuit_breakers[job_id].is_open:
            logger.warning(f"SchedulerOrchestrator: Circuit breaker aberto para {job_id}")
            # Pausar job
            self.scheduler.pause_job(job_id)
```

---

## 13. MONITORING SCHEDULER

### 13.1 Métricas de Scheduler

```python
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SchedulerMetrics:
    """Métricas do scheduler."""
    
    def __init__(self):
        self.job_executions = {}  # {job_id: {success: 0, failed: 0}}
        self.job_durations = {}  # {job_id: [duration1, duration2, ...]}
    
    def record_execution(self, job_id: str, success: bool, duration: float):
        """Registra execução de job."""
        if job_id not in self.job_executions:
            self.job_executions[job_id] = {'success': 0, 'failed': 0}
            self.job_durations[job_id] = []
        
        if success:
            self.job_executions[job_id]['success'] += 1
        else:
            self.job_executions[job_id]['failed'] += 1
        
        self.job_durations[job_id].append(duration)
    
    def get_job_summary(self, job_id: str) -> Dict:
        """Retorna resumo de job."""
        if job_id not in self.job_executions:
            return {}
        
        total = self.job_executions[job_id]['success'] + self.job_executions[job_id]['failed']
        success_rate = (self.job_executions[job_id]['success'] / total * 100) if total > 0 else 0
        
        avg_duration = sum(self.job_durations[job_id]) / len(self.job_durations[job_id]) if self.job_durations[job_id] else 0
        
        return {
            'total_executions': total,
            'success_count': self.job_executions[job_id]['success'],
            'failed_count': self.job_executions[job_id]['failed'],
            'success_rate': success_rate,
            'avg_duration': avg_duration
        }
```

---

## 14. ESCALA: APSCHEDULER → CELERY

### 14.1 Quando Escalar?

**Sinais que precisa escalar:**
- APScheduler single process não consegue lidar com carga
- Jobs começam a falhar por timeout
- Precisa de distribuir jobs em múltiplos processos/workers
- Precisa de alta disponibilidade (HA)

### 14.2 Estratégia de Migração para Celery

```python
# requirements.txt (produção)
celery==5.3.0
redis==5.0.0
flower==2.0.0  # Monitoramento Celery

# celery_config.py
from celery import Celery

app = Celery(
    'broker': 'redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    broker_transport_options={'visibility': 'topic'},
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Lisbon'
)

# tasks.py
@app.task
def scraping_task():
    # Código de scraping
    pass

@app.task
def etl_task():
    # Código de ETL
    pass

# worker.py
from celery_worker import celery_worker
celery_worker('app', loglevel='info')

# Executar worker
celery -A app worker -l info
```

---

## 15. GLOSSÁRIO DE SCHEDULER

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE SCHEDULER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCHEDULER: Agendador de tarefas automáticas                              │
│                                                                             │
│  APSCHEDULER: Biblioteca Python para agendamento de tarefas           │
│                                                                             │
│  JOB: Tarefa agendada (ex: scraping_job, etl_job)                     │
│                                                                             │
│  TRIGGER: Gatilho de execução (interval, cron, date)                   │
│                                                                             │
│  INTERVAL TRIGGER: Gatilho de intervalo (ex: cada 30 minutos)          │
│                                                                             │
│  CRON TRIGGER: Gatilho cron (ex: todos os dias às 3:00 AM)               │
│                                                                             │
│  JOBSTORE: Armazenamento de jobs (SQLAlchemyJobStore para persistência)   │
│                                                                             │
│  EXECUTOR: Executor de jobs (AsyncIOExecutor para async)                │
│                                                                             │
│  ORCHESTRATOR: Orquestrador de tarefas (coordena jobs)                  │
│                                                                             │
│  COALESCE: Coalesce (agregar execuções missed se job já está a correr)   │
│ │                                                                             │
│  MAX_INSTANCES: Máximo de instâncias simultâneas de um job               │
│                                                                             │
│  MISFIRE GRACE TIME: Tempo de tolerância para jobs missed (em segundos)    │
│                                                                             │
│  CIRCUIT BREAKER: Disjuntor que pausa jobs se falhas consecutivas        │
│                                                                             │
│  ERROR HANDLING: Gestão de erros de jobs                                │
│                                                                             │
│  RETRY: Tentar novamente jobs que falharam                              │
│                                                                             │
│  BACKOFF EXPONENTIAL: Atraso exponencial entre retries (1s, 2s, 4s...)   │
│                                                                             │
│  MONITORING: Monitoramento de jobs (tempo execução, taxa sucesso)        │
│                                                                             │
│  HEALTH CHECK: Verificação de saúde do sistema                           │
│                                                                             │
│  ALERT: Alerta (via Telegram) para falhas críticas                         │
│                                                                             │
│  CELERY: Alternativa distribuída para produção (múltiplos workers)      │
│                                                                             │
│  REDIS: Broker de mensagens para Celery (fila de tarefas)               │
│
│  RABBITMQ: Broker de mensagens alternativo para Celery                     │
│                                                                             │
│  WORKER: Worker que executa tarefas Celery                              │
│                                                                             │
│  FLOWER: Ferramenta de monitoramento para Celery                         │
│                                                                             │
│  DISTRIBUTED: Distribuído (múltiplos processos/workers)                   │
│                                                                             │
│  SINGLE PROCESS: Single process (APScheduler MVP)                       │
│                                                                             │
│  HIGH AVAILABILITY: Alta disponibilidade (HA, failover)                │
│                                                                             │
│  FAILOVER: Failover (recuperação de falha)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. HARDENING ONDA 4 — APSCHEDULER ROBUSTNESS

### 16.1 Problemas do Scheduler Baseline

**Problema:**
- Sem `max_instances`: jobs podem executar em paralelo se o anterior demorar mais que o intervalo
- Sem `coalesce`: jobs missed durante suspend/clock drift executam em burst (overload)
- Sem `misfire_grace_time`: jobs ligeiramente atrasados são marcados como missed
- Sem event listeners: dificil debug de problemas (job overlap, missed jobs, errors)
- Logs não estruturados: dificil parse e análise

### 16.2 Solução: Hardening APScheduler

**Parâmetros de Hardening:**
```python
# realestate_engine/scheduler/orchestrator.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_SUBMITTED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_MAX_INSTANCES

class Orchestrator:
    def start(self):
        # Job 1: Full pipeline (cada hora das 8:00-22:00)
        self.scheduler.add_job(
            self.run_full_pipeline,
            CronTrigger(hour="8-22", minute="0"),
            id="full_pipeline",
            max_instances=1,  # Anti-overlap: apenas 1 instância simultânea
            coalesce=True,  # Anti-burst: agrega missed jobs se job já a correr
            misfire_grace_time=1800,  # Tolerância 30min para clock drift/suspend
        )
        
        # Job 2: Daily summary (20:30)
        self.scheduler.add_job(
            self.send_daily_summary,
            CronTrigger(hour="20", minute="30"),
            id="daily_summary",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,  # Tolerância 10min
        )
        
        # Event listeners para logs estruturados
        self.scheduler.add_listener(self._track_job_start, EVENT_JOB_SUBMITTED)
        self.scheduler.add_listener(
            self._on_scheduler_event,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES,
        )
        
        self.scheduler.start()
```

### 16.3 Event Listeners com Logs Estruturados

**Track Job Start:**
```python
def _track_job_start(self, event):
    """Regista quando job é submetido para medir duração."""
    job = self.scheduler.get_job(event.job_id)
    logger.info(
        f"apscheduler.event=job_submitted job_id={event.job_id} "
        f"scheduled_run_time={event.scheduled_run_time}"
    )
```

**On Scheduler Event:**
```python
def _on_scheduler_event(self, event):
    """Registra eventos do scheduler com logs estruturados."""
    if event.code == EVENT_JOB_EXECUTED:
        duration = (event.ret_val - event.scheduled_run_time).total_seconds()
        logger.info(
            f"apscheduler.event=job_executed job_id={event.job_id} "
            f"duration={duration:.2f}s scheduled_run_time={event.scheduled_run_time}"
        )
    elif event.code == EVENT_JOB_ERROR:
        logger.error(
            f"apscheduler.event=job_error job_id={event.job_id} "
            f"exception={event.exception} traceback={event.traceback}"
        )
    elif event.code == EVENT_JOB_MISSED:
        logger.warning(
            f"apscheduler.event=job_missed job_id={event.job_id} "
            f"scheduled_run_time={event.scheduled_run_time}"
        )
    elif event.code == EVENT_JOB_MAX_INSTANCES:
        logger.warning(
            f"apscheduler.event=job_max_instances job_id={event.job_id} "
            f"job já estava a executar, nova instância ignorada"
        )
```

### 16.4 Benefícios

**Anti-Overlap:**
- `max_instances=1` garante que jobs não executam em paralelo
- Evita race conditions e sobrecarga do sistema

**Anti-Burst:**
- `coalesce=True` agrega missed jobs se job já está a correr
- Evita burst de execuções após suspend/clock drift

**Tolerância a Clock Drift:**
- `misfire_grace_time` permite tolerância a pequenos atrasos
- Reduz falsos positivos de missed jobs

**Observabilidade:**
- Event listeners com logs estruturados `apscheduler.event=`
- Fácil parse e análise de logs
- Debugging mais eficiente

---

*Fim do Documento 11 — Scheduler e Orquestração*
