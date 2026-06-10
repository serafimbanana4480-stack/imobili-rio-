"""Health checks for Real Estate Opportunity Engine.

Enhanced with:
- Redis connectivity check
- External API availability (INE, geocoding)
- Disk space check
- Memory usage check
- Scheduler job queue health
- Historical health tracking
"""
import time
import psutil
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List
from sqlalchemy import text
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.utils.config import config


class HealthCheck:
    """Health check system for monitoring system components."""
    
    def __init__(self):
        self.checks: Dict[str, Any] = {}
        self.db_repo = DatabaseRepository()
        self.history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start = time.time()
            with self.db_repo.Session() as session:
                session.execute(text("SELECT 1"))
            latency_ms = (time.time() - start) * 1000
            return {"status": "healthy", "latency_ms": round(latency_ms, 2)}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity with graceful degradation.

        Redis is an optional caching layer; its absence should not block the pipeline.
        """
        # Skip if Redis URL is default localhost and likely not configured
        if config.redis_url in ("redis://localhost:6379/0", "", None):
            return {"status": "degraded", "note": "Redis not configured (optional)"}

        try:
            import redis
            start = time.time()
            r = redis.from_url(config.redis_url, socket_connect_timeout=2)
            r.ping()
            latency_ms = (time.time() - start) * 1000
            return {"status": "healthy", "latency_ms": round(latency_ms, 2)}
        except ImportError:
            return {"status": "degraded", "note": "Redis not installed (optional)"}
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {"status": "degraded", "error": str(e), "note": "Redis is optional for caching"}
    
    async def check_external_apis(self) -> Dict[str, Any]:
        """Check external API availability (INE, geocoding)."""
        results = {
            "status": "healthy",
            "checks": {}
        }
        
        # Check INE API availability
        try:
            import httpx
            start = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.ine.pt/", follow_redirects=True)
                latency_ms = (time.time() - start) * 1000
                if response.status_code < 500:
                    results["checks"]["ine_api"] = {"status": "healthy", "latency_ms": round(latency_ms, 2)}
                else:
                    results["checks"]["ine_api"] = {"status": "unhealthy", "status_code": response.status_code}
                    results["status"] = "degraded"
        except Exception as e:
            results["checks"]["ine_api"] = {"status": "unhealthy", "error": str(e)}
            results["status"] = "degraded"
        
        # Check geocoding API (Nominatim as example)
        try:
            import httpx
            start = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search?q=Porto&format=json",
                    headers={"User-Agent": "RealEstateEngine/1.0"},
                    timeout=5.0
                )
                latency_ms = (time.time() - start) * 1000
                if response.status_code == 200:
                    results["checks"]["geocoding_api"] = {"status": "healthy", "latency_ms": round(latency_ms, 2)}
                else:
                    results["checks"]["geocoding_api"] = {"status": "unhealthy", "status_code": response.status_code}
                    results["status"] = "degraded"
        except Exception as e:
            results["checks"]["geocoding_api"] = {"status": "unhealthy", "error": str(e)}
            results["status"] = "degraded"
        
        return results
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space availability."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            percent_used = disk.percent
            
            if percent_used > 90:
                status = "unhealthy"
            elif percent_used > 75:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_used": percent_used
            }
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            percent_used = memory.percent
            
            if percent_used > 90:
                status = "unhealthy"
            elif percent_used > 75:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "used_gb": round(used_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_used": percent_used
            }
        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_scheduler(self) -> Dict[str, Any]:
        """Check scheduler status and job queue health."""
        try:
            # Check recent job executions across all pipeline phases
            job_names = ["spider_manager", "pipeline_etl", "valuation_engine",
                         "scoring_engine", "notification_engine"]
            total_recent = 0
            total_failed = 0
            failed_details = []

            for jn in job_names:
                recent = self.db_repo.get_recent_job_executions(jn, limit=3)
                total_recent += len(recent)
                for j in recent:
                    if j.status in ("error", "failed"):
                        total_failed += 1
                        failed_details.append(f"{jn}: {j.status}")

            if total_failed > 3:
                return {
                    "status": "unhealthy",
                    "note": f"{total_failed} falhas recentes: {', '.join(failed_details[:3])}",
                    "fix": "Verifica os logs em ⚙️ Sistema → Debug Logs para detalhes dos erros"
                }

            if total_recent == 0:
                return {
                    "status": "warning",
                    "note": "Nenhuma execução de job registada",
                    "fix": "Executa o pipeline: ▶️ Executar Scraping ou Pipeline Completo"
                }

            return {
                "status": "healthy",
                "recent_jobs": total_recent,
                "failed_jobs": total_failed
            }
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "fix": "Verifica a conexão à base de dados"}
    
    def check_scraping(self) -> Dict[str, Any]:
        """Check scraping health by looking at last run."""
        try:
            # The actual job name stored in DB is "spider_manager", not "scraping"
            last_run = self.db_repo.get_last_job_execution("spider_manager")
            if not last_run:
                return {
                    "status": "warning",
                    "note": "Sem histórico de scraping",
                    "fix": "Executa o scraping: 🔄 Scraping → ▶️ Executar Scraping Completo"
                }

            hours_since = (datetime.now(UTC) - last_run.started_at).total_seconds() / 3600

            if hours_since > 24:
                return {
                    "status": "unhealthy",
                    "note": f"Último scraping há {hours_since:.0f}h (deveria ser <24h)",
                    "fix": "Executa o scraping ou configura o scheduler para correr automaticamente"
                }
            elif hours_since > 6:
                return {
                    "status": "warning",
                    "note": f"Último scraping há {hours_since:.1f}h",
                    "fix": "Considera executar o scraping para manter os dados atualizados"
                }

            return {
                "status": "healthy",
                "last_run": str(last_run.started_at),
                "hours_ago": round(hours_since, 1),
                "records": last_run.records_processed
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "fix": "Verifica a base de dados e os logs"}
    
    def record_history(self, checks: Dict[str, Any]) -> None:
        """Record health check results in history."""
        self.history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "overall": checks.get("overall", "unknown"),
            "checks": checks
        })
        
        # Keep only recent history
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical health check results."""
        return self.history[-limit:]
    
    def get_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        start = time.time()
        
        self.checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "external_apis": self.check_external_apis(),
            "disk_space": self.check_disk_space(),
            "memory": self.check_memory_usage(),
            "scheduler": self.check_scheduler(),
            "scraping": self.check_scraping(),
            "timestamp": time.time(),
            "overall": "healthy"
        }
        
        # Determine overall status
        # Redis "degraded" is optional and should not drag overall to unhealthy
        critical_statuses = [
            self.checks["database"].get("status"),
            self.checks["external_apis"].get("status"),
            self.checks["disk_space"].get("status"),
            self.checks["memory"].get("status"),
            self.checks["scheduler"].get("status"),
            self.checks["scraping"].get("status"),
        ]
        redis_status = self.checks["redis"].get("status")

        if "unhealthy" in critical_statuses:
            self.checks["overall"] = "unhealthy"
        elif "warning" in critical_statuses or "degraded" in critical_statuses:
            self.checks["overall"] = "degraded"
        elif redis_status == "degraded":
            # Redis is optional — degraded alone is still healthy overall
            self.checks["overall"] = "healthy"
        else:
            self.checks["overall"] = "healthy"
        
        self.checks["latency_ms"] = round((time.time() - start) * 1000, 2)
        
        # Record in history
        self.record_history(self.checks)
        
        return self.checks
