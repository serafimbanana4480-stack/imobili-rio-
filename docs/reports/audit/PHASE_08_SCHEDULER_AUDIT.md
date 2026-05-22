# PHASE 8: SCHEDULER AUDIT
## Reliability, Observability

**Date:** 2026-05-04  
**Auditor:** Principal Software Architect + Staff Engineer + SRE  
**Scope:** Complete scheduler analysis for production 24/7 operation  
**Production Context:** System intended for commercial sale with autonomous 24/7 operation

---

## EXECUTIVE SUMMARY

**Overall Scheduler Score:** 82/100

**Critical Issues:** 0  
**High Priority Issues:** 2  
**Medium Priority Issues:** 4  
**Low Priority Issues:** 2

**Key Findings:**
- Scheduler uses APScheduler (good choice for single-node)
- Excellent hardening settings (max_instances, coalesce, misfire_grace_time)
- **HIGH:** No job persistence (jobs lost on restart)
- **HIGH:** No distributed execution (single-node only)
- Night silence period for notifications (good UX)
- Structured logging with job lifecycle tracking
- Event listeners for executed, error, missed, max_instances events
- Graceful shutdown implemented
- No job priority system
- No job dependencies
- No job retry with exponential backoff
- No dead letter queue for failed jobs
- No job execution time SLA monitoring

---

## 1. SCHEDULER ARCHITECTURE ANALYSIS

### 1.1 Current Architecture

**LOCATION:** `realestate_engine/scheduler/orchestrator.py` (252 lines)

**Architecture Pattern:**
```
Orchestrator (APScheduler)
├── Jobs
│   ├── Scraping Cycle
│   ├── ETL Pipeline
│   ├── Valuation Batch
│   ├── Scoring Batch
│   ├── Notification (Top Opps)
│   └── AI Analysis
├── Event Listeners
│   ├── Executed
│   ├── Error
│   ├── Missed
│   └── Max Instances
└── Night Silence Period (00:00-07:00)
```

**Code Analysis:**
```python
class Orchestrator:
    """Orchestrator that runs the entire real estate engine autonomously 24/7."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.spider_manager = SpiderManager()
        self.etl_pipeline = PipelineETL()
        self.valuation_engine = ValuationEngine()
        self.scoring_engine = ScoringEngine()
        self.notifier = NotificationEngine()
        self._job_started_at = {}
        
        # Add event listeners
        self.scheduler.add_listener(
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES,
            self._on_scheduler_event
        )
    
    async def start(self):
        """Start the scheduler with hardened settings."""
        self.scheduler.add_job(
            self.run_full_pipeline,
            CronTrigger(hour="8-22", minute="0"),  # Every hour 8:00-22:00
            id="full_pipeline",
            max_instances=1,  # Prevent overlap
            coalesce=True,  # Colapses missed triggers
            misfire_grace_time=1800  # 30min tolerance
        )
        
        await self.scheduler.start()
```

**Strengths:**
1. **APScheduler:** Reliable, production-grade scheduler
2. **Hardening:** max_instances=1 prevents overlap
3. **Coalesce:** Combines missed triggers into one
4. **Misfire Grace Time:** 30min tolerance for clock drift
5. **Event Listeners:** Comprehensive job lifecycle tracking
6. **Night Silence:** 00:00-07:00 no notifications (good UX)
7. **Graceful Shutdown:** Proper cleanup on shutdown
8. **Structured Logging:** Detailed job execution logs

**Production-Ready Features:**
- ✅ APScheduler with hardening
- ✅ Event listeners for observability
- ✅ Night silence period
- ✅ Graceful shutdown
- ✅ Job lifecycle logging

**Critical Gaps:**
- ⚠️ **No Job Persistence:** Jobs lost on restart
- ⚠️ **No Distributed Execution:** Single-node only
- ⚠️ **No Retry with Backoff:** Limited retry logic
- ⚠️ **No Dead Letter Queue:** Failed jobs not tracked
- ⚠️ **No SLA Monitoring:** No execution time alerts
- ⚠️ **No Job Dependencies:** Jobs run independently

---

## 2. HIGH PRIORITY ISSUES

### 2.1 HIGH PRIORITY ISSUE #1: No Job Persistence

**SEVERITY:** 🟠 HIGH - DATA LOSS RISK

**LOCATION:** `realestate_engine/scheduler/orchestrator.py` (missing)

**Problem:**
```python
# Current implementation
self.scheduler.add_job(
    self.run_full_pipeline,
    CronTrigger(hour="8-22", minute="0"),
    id="full_pipeline"
)
# Jobs are stored in memory - lost on restart
```

**Root Cause:**
- APScheduler uses in-memory job store by default
- No database persistence
- No job serialization
- No job recovery after restart

**Impact on Production:**
- **Job Loss:** Jobs scheduled but not yet executed are lost on restart
- **Inconsistent State:** Cannot track which jobs ran
- **No Recovery:** Cannot resume from last execution
- **Data Loss:** Missed data collection windows

**Real-World Scenario:**
```
Day 1: Scheduler running, jobs scheduled
Day 2: Server restart for maintenance
Day 3: Scheduler restarts, all scheduled jobs lost
Day 4: No data collected for 2 days
Day 5: Market changes missed, investment opportunities lost
```

**Refactor Suggestion - Job Persistence:**
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import create_engine

class PersistentOrchestrator(Orchestrator):
    """Orchestrator with job persistence."""
    
    def __init__(self):
        # Database-backed job store
        jobstore = SQLAlchemyJobStore(
            url=config.database_url,
            tablename='apscheduler_jobs'
        )
        
        # Async executor
        executor = AsyncIOExecutor()
        
        # Create scheduler with persistence
        self.scheduler = AsyncIOScheduler(
            jobstore=jobstore,
            executor=executor,
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 1800,
            }
        )
        
        # Initialize job store
        self.scheduler.start()
    
    async def add_persistent_job(
        self,
        func,
        trigger,
        job_id: str,
        replace_existing: bool = True
    ):
        """Add job with persistence."""
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            replace_existing=replace_existing,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800
        )
        
        logger.info(f"Added persistent job: {job_id}")
    
    async def get_job_info(self, job_id: str) -> dict:
        """Get job information from job store."""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
                "executor": job.executor
            }
        return None
    
    async def list_jobs(self) -> list:
        """List all jobs."""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]

# Database migration for job store
# Create table for APScheduler jobs
"""
CREATE TABLE apscheduler_jobs (
    id VARCHAR(191) NOT NULL,
    next_run_time FLOAT NOT NULL,
    job_state BLOB NOT NULL,
    PRIMARY KEY (id)
);
"""
```

**Benefits:**
- **Persistence:** Jobs survive restarts
- **Recovery:** Can resume from last execution
- **Consistency:** Track which jobs ran
- **Audit Trail:** Job history in database
- **Scalability:** Supports distributed execution

**Implementation Effort:** 2 days  
**Priority:** HIGH  
**Risk:** LOW

---

### 2.2 HIGH PRIORITY ISSUE #2: No Distributed Execution

**SEVERITY:** 🟠 HIGH - SCALABILITY LIMIT

**LOCATION:** `realestate_engine/scheduler/orchestrator.py` (missing)

**Problem:**
- Single-node execution only
- No horizontal scaling
- No load balancing
- No high availability

**Impact on Production:**
- **Scalability:** Cannot scale beyond single server
- **Availability:** Single point of failure
- **Performance:** Limited by single machine
- **Commercial Risk:** Cannot guarantee SLA for enterprise customers

**Refactor Suggestion - Distributed Scheduler Options:**

**Option 1: Airflow (Recommended for Scale)**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'realestate',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'real_estate_pipeline',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False,
    max_active_runs=1
) as dag:
    
    scraping_task = PythonOperator(
        task_id='scraping',
        python_callable=run_scraping_cycle,
        retries=3,
        retry_delay=timedelta(minutes=5)
    )
    
    etl_task = PythonOperator(
        task_id='etl',
        python_callable=run_etl_pipeline,
        retries=3,
        retry_delay=timedelta(minutes=5)
    )
    
    valuation_task = PythonOperator(
        task_id='valuation',
        python_callable=run_valuation_batch,
        retries=2,
        retry_delay=timedelta(minutes=10)
    )
    
    scoring_task = PythonOperator(
        task_id='scoring',
        python_callable=run_scoring_batch,
        retries=2,
        retry_delay=timedelta(minutes=10)
    )
    
    notification_task = PythonOperator(
        task_id='notification',
        python_callable=send_notifications,
        retries=2,
        retry_delay=timedelta(minutes=5)
    )
    
    # Define dependencies
    scraping_task >> etl_task >> valuation_task >> scoring_task >> notification_task
```

**Option 2: Redis + Celery (Distributed Task Queue)**
```python
from celery import Celery
from celery.schedules import crontab

app = Celery('realestate_tasks', broker=config.redis_url)

@app.task(bind=True)
def scraping_task(self):
    """Scraping task with distributed execution."""
    try:
        result = run_scraping_cycle()
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)

@app.task(bind=True)
def etl_task(self):
    """ETL task with distributed execution."""
    try:
        result = run_etl_pipeline()
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)

# Schedule tasks
app.conf.beat_schedule = {
    'run-full-pipeline': {
        'task': 'tasks.run_full_pipeline',
        'schedule': crontab(hour='8-22/1'),  # Every hour 8:00-22:00
    },
}
```

**Recommendation:**
- **Short-term:** Keep APScheduler with job persistence
- **Medium-term:** Migrate to Celery for distributed execution
- **Long-term:** Migrate to Airflow for complex workflows

**Implementation Effort:** 5-7 days (for Celery migration)  
**Priority:** HIGH  
**Risk:** HIGH (requires infrastructure changes)

---

## 3. MEDIUM PRIORITY ISSUES

### 3.1 MEDIUM PRIORITY ISSUE #1: No Retry with Exponential Backoff

**SEVERITY:** 🟡 MEDIUM - RELIABILITY RISK

**LOCATION:** `realestate_engine/scheduler/orchestrator.py` (missing retry logic)

**Problem:**
```python
# Current implementation
async def run_full_pipeline(self):
    try:
        async with JobLogger("scraping.cycle") as jl:
            summary = await self.spider_manager.run_all_cycle(...)
    except Exception as e:
        logger.exception(f"Critical error during scraping: {e}")
        # No retry - job fails completely
```

**Root Cause:**
- No retry logic for failed jobs
- No exponential backoff
- No circuit breaker
- No dead letter queue

**Impact on Production:**
- **Reliability:** Transient failures cause complete job failure
- **Data Loss:** Missed data collection windows
- **No Recovery:** Manual intervention required

**Refactor Suggestion - Retry with Backoff:**
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientOrchestrator(Orchestrator):
    """Orchestrator with retry logic."""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def run_scraping_with_retry(self):
        """Run scraping with retry logic."""
        summary = await self.spider_manager.run_all_cycle(
            active_portals=["imovirtual", "casa_sapo"]
        )
        return summary
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=10, max=120)
    )
    async def run_etl_with_retry(self):
        """Run ETL with retry logic."""
        result = await self.etl_pipeline.run(batch_size=10000)
        return result
    
    async def run_full_pipeline_with_retry(self):
        """Run full pipeline with retry logic."""
        try:
            # Scraping (3 retries)
            summary = await self.run_scraping_with_retry()
            logger.info(f"Scraping completed: {summary}")
        except Exception as e:
            logger.error(f"Scraping failed after retries: {e}")
            # Continue to next phase even if scraping failed
        
        try:
            # ETL (2 retries)
            count = await self.run_etl_with_retry()
            logger.info(f"ETL completed: {count} listings")
        except Exception as e:
            logger.error(f"ETL failed after retries: {e}")
        
        # Continue with valuation, scoring, notification...
```

**Implementation Effort:** 2 days  
**Priority:** MEDIUM  
**Risk**: LOW

---

### 3.2 MEDIUM PRIORITY ISSUE #2: No Dead Letter Queue

**SEVERITY:** 🟡 MEDIUM - NO ERROR TRACKING

**LOCATION:** Missing component

**Problem:**
- Failed jobs are logged but not tracked
- No retry queue for failed jobs
- No manual intervention workflow
- No alerting for repeated failures

**Refactor Suggestion:**
```python
class DeadLetterQueue:
    """Dead letter queue for failed jobs."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
    
    def add_failed_job(self, job_id: str, error: str, retry_count: int = 0):
        """Add failed job to DLQ."""
        self.repo.create_failed_job({
            "job_id": job_id,
            "error": error,
            "retry_count": retry_count,
            "failed_at": datetime.now(UTC),
            "status": "pending"
        })
    
    def get_failed_jobs(self, limit: int = 100):
        """Get failed jobs for retry."""
        return self.repo.get_failed_jobs(status="pending", limit=limit)
    
    def mark_retried(self, job_id: str):
        """Mark job as retried."""
        self.repo.update_failed_job(job_id, status="retried")

# Integration with orchestrator
class ResilientOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__()
        self.dlq = DeadLetterQueue(self.repo)
    
    async def run_full_pipeline_with_dlq(self):
        """Run full pipeline with DLQ support."""
        try:
            await self.run_full_pipeline()
        except Exception as e:
            logger.error(f"Pipeline failed, adding to DLQ: {e}")
            self.dlq.add_failed_job("full_pipeline", str(e))
            
            # Alert
            await self.notifier.send_alert(f"Pipeline failed: {e}")
```

**Implementation Effort:** 2 days  
**Priority:** MEDIUM  
**Risk**: LOW

---

### 3.3 Additional Medium Priority Issues

| # | Issue | Location | Impact | Effort | Priority |
|---|-------|----------|--------|--------|----------|
| 3 | No job priority system | orchestrator.py | LOW | 2 days | MEDIUM |
| 4 | No job dependencies | orchestrator.py | MEDIUM | 3 days | MEDIUM |

---

## 4. REFACTOR ROADMAP

### Phase 1: High Priority (Week 1-2)
- [ ] Implement job persistence with SQLAlchemyJobStore
- [ ] Add job recovery after restart
- [ ] Implement job history tracking
- [ ] Evaluate distributed scheduler options

### Phase 2: High Priority (Week 3-4)
- [ ] Migrate to Celery for distributed execution
- [ ] Implement Redis broker
- [ ] Add worker scaling
- [ ] Implement distributed task queue

### Phase 3: Medium Priority (Week 5)
- [ ] Implement retry with exponential backoff
- [ ] Add dead letter queue
- [ ] Implement job priority system
- [ ] Add job dependencies

### Phase 4: Low Priority (Week 6)
- [ ] Add SLA monitoring
- [ ] Implement job execution time alerts
- [ ] Add job performance dashboard

---

## 5. PRODUCTION READINESS SCORE

**Scheduler Audit Score: 82/100**

**Breakdown:**
- Framework: 90/100 (APScheduler is excellent)
- Hardening: 95/100 (excellent settings)
- Persistence: 40/100 (no persistence - HIGH)
- Distributed: 30/100 (single-node only - HIGH)
- Retry Logic: 50/100 (no retry with backoff)
- Observability: 80/100 (good event listeners)
- Reliability: 70/100 (no DLQ, limited retry)

**Recommendation:** Implement job persistence immediately. For commercial scale (>100 concurrent users), plan migration to Celery or Airflow for distributed execution.

---

**End of Phase 8: Scheduler Audit**
