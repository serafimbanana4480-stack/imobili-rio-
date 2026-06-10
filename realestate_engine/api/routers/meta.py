"""Meta Layer API endpoints for system self-auditing and reporting."""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger
import re
from pathlib import Path

from realestate_engine.meta.tech_audit_engine import TechAuditEngine
from realestate_engine.monitoring.model_monitor import ModelMonitor
from realestate_engine.monitoring.intelligent_alerts import IntelligentAlertEngine
from realestate_engine.monitoring.cost_tracker import CostTracker
from realestate_engine.meta.benchmark import BenchmarkEngine
from realestate_engine.api.middleware.auth import optional_auth
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS

router = APIRouter()


class AuditResponse(BaseModel):
    """Response schema for audit endpoint."""
    status: str
    report_filename: str
    overall_status: str
    findings_count: int
    stack_versions: Dict[str, Any]


class DriftAlertsResponse(BaseModel):
    """Response schema for drift alerts."""
    alerts: List[Dict[str, Any]]
    count: int


class IntelligentAlertsResponse(BaseModel):
    """Response schema for intelligent alerts."""
    alerts: List[Dict[str, Any]]
    count: int


class CostSummaryResponse(BaseModel):
    """Response schema for cost summary."""
    summary: Dict[str, Any]
    cost_per_lead: Optional[float]


class BenchmarkSummaryResponse(BaseModel):
    """Response schema for benchmark summary."""
    name: str
    history: List[Dict[str, Any]]
    summary: Dict[str, Any]


def _sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove any path separators and parent directory references
    name = re.sub(r'[\\/]', '_', name)
    name = name.replace('..', '_')
    # Keep only safe characters
    name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)
    return name


@router.post("/audit", response_model=AuditResponse)
@rate_limit(RATE_LIMITS["strict"])
async def run_audit(
    request: Request,
    current_user: dict = Depends(optional_auth)
):
    """Trigger a read-only technical audit and return the report."""
    try:
        engine = TechAuditEngine(project_root=".")
        report = engine.run_audit()
        path = engine.save_report(report)
        # Sanitize and return only filename
        safe_filename = _sanitize_filename(Path(path).name)
        return AuditResponse(
            status="success",
            report_filename=safe_filename,
            overall_status=report.overall_status,
            findings_count=len(report.findings),
            stack_versions=report.stack_versions,
        )
    except Exception as e:
        logger.error(f"Meta audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift-alerts", response_model=DriftAlertsResponse)
@rate_limit(RATE_LIMITS["default"])
async def get_drift_alerts(
    request: Request,
    model_name: str = None,
    limit: int = Query(50, ge=1, le=1000),
    current_user: dict = Depends(optional_auth),
):
    """Get recent model drift alerts."""
    try:
        monitor = ModelMonitor()
        alerts = monitor.get_recent_alerts(model_name=model_name, limit=limit)
        return DriftAlertsResponse(alerts=alerts, count=len(alerts))
    except Exception as e:
        logger.error(f"Drift alerts query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=IntelligentAlertsResponse)
@rate_limit(RATE_LIMITS["default"])
async def get_intelligent_alerts(
    request: Request,
    severity: str = None,
    limit: int = Query(50, ge=1, le=1000),
    current_user: dict = Depends(optional_auth),
):
    """Get recent intelligent alerts."""
    try:
        engine = IntelligentAlertEngine()
        alerts = engine.get_recent_alerts(severity=severity, limit=limit)
        return IntelligentAlertsResponse(alerts=alerts, count=len(alerts))
    except Exception as e:
        logger.error(f"Intelligent alerts query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs", response_model=CostSummaryResponse)
@rate_limit(RATE_LIMITS["default"])
async def get_cost_summary(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(optional_auth),
):
    """Get cost tracking summary for the specified period."""
    try:
        tracker = CostTracker()
        summary = tracker.get_summary(days=days)
        cpl = tracker.get_cost_per_lead(days=days)
        return CostSummaryResponse(summary=summary, cost_per_lead=cpl)
    except Exception as e:
        logger.error(f"Cost summary query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks/{name}", response_model=BenchmarkSummaryResponse)
@rate_limit(RATE_LIMITS["default"])
async def get_benchmark_summary(
    request: Request,
    name: str,
    current_user: dict = Depends(optional_auth),
):
    """Get benchmark history and summary for a named operation."""
    try:
        engine = BenchmarkEngine()
        history = engine.get_history(name, limit=100)
        summary = engine.get_summary(name)
        return BenchmarkSummaryResponse(name=name, history=history, summary=summary)
    except Exception as e:
        logger.error(f"Benchmark query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
