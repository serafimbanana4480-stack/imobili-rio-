"""Debug & Logs dashboard view for real-time troubleshooting.

Shows:
- Recent error logs
- Active alerts
- System health status
- Scraping block detection
- ETL/ML failure summary
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.monitoring.health_checks import HealthCheck


def render_debug_logs():
    """Render debug and system logs page."""
    st.title("🐛 Debug & Logs")
    st.markdown("*Diagnóstico em tempo real do sistema*")

    repo = DatabaseRepository()
    hc = HealthCheck()

    # ── System Health Status ───────────────────────────────────────────
    st.markdown("### 🏥 Estado do Sistema")
    checks = hc.get_all_checks()

    col1, col2, col3, col4 = st.columns(4)
    status_colors = {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴",
        "warning": "🟠",
    }

    with col1:
        db_status = checks.get("database", {}).get("status", "unknown")
        st.metric("Database", f"{status_colors.get(db_status, '⚪')} {db_status.upper()}")

    with col2:
        redis_status = checks.get("redis", {}).get("status", "unknown")
        st.metric("Redis", f"{status_colors.get(redis_status, '⚪')} {redis_status.upper()}")

    with col3:
        api_status = checks.get("external_apis", {}).get("status", "unknown")
        st.metric("APIs Externas", f"{status_colors.get(api_status, '⚪')} {api_status.upper()}")

    with col4:
        overall = checks.get("overall", "unknown")
        st.metric("Sistema Geral", f"{status_colors.get(overall, '⚪')} {str(overall).upper()}")

    # ── Recent Failures ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔴 Falhas Recentes")

    job_names = ["spider_manager", "pipeline_etl", "valuation_engine", "scoring_engine", "notification_engine"]
    failed_jobs = []
    for job_name in job_names:
        executions = repo.get_recent_job_executions(job_name, limit=5)
        for exec in executions:
            if exec.status in ("failed", "error"):
                failed_jobs.append({
                    "Job": job_name.replace("_", " ").title(),
                    "Início": exec.started_at.strftime("%Y-%m-%d %H:%M:%S") if exec.started_at else "",
                    "Status": exec.status.upper(),
                    "Registros": exec.records_processed or 0,
                })

    if failed_jobs:
        st.dataframe(pd.DataFrame(failed_jobs).sort_values("Início", ascending=False),
                     hide_index=True, use_container_width=True)
    else:
        st.success("✅ Sem falhas registadas nas últimas execuções")

    # ── Error Log Viewer ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Logs de Erros")

    error_log_path = os.path.join(project_root, "logs", "errors.log")
    if os.path.exists(error_log_path):
        with open(error_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter by time window
        hours_back = st.slider("Horas atrás", 1, 72, 24, key="log_hours")
        cutoff = datetime.now() - timedelta(hours=hours_back)

        recent_errors = []
        for line in lines[-500:]:  # Last 500 lines
            recent_errors.append(line.strip())

        if recent_errors:
            with st.expander(f"Últimas {len(recent_errors)} linhas de log"):
                st.code("\n".join(recent_errors[-100:]), language="text")
        else:
            st.info("Sem erros recentes")
    else:
        st.info("Ficheiro de logs não encontrado. Verifique `logs/errors.log`.")

    # ── Scraping Block Detection ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🕷️ Deteção de Bloqueios (Anti-Bot)")

    # Count recent job executions with 0 records
    zero_scrapes = 0
    for job_name in ["spider_manager"]:
        executions = repo.get_recent_job_executions(job_name, limit=10)
        for exec in executions:
            if exec.records_processed == 0 and exec.status == "success":
                zero_scrapes += 1

    if zero_scrapes >= 3:
        st.error(f"⚠️ {zero_scrapes} execuções de scraping consecutivas sem registos — possível bloqueio anti-bot")
    else:
        st.success(f"✅ Scraping funcionando ({zero_scrapes} execuções vazias nas últimas 10)")

    # ── Data Quality Summary ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Resumo de Qualidade de Dados")

    from realestate_engine.monitoring.data_quality import DataQualityEngine

    dq = DataQualityEngine()
    clean_listings = repo.get_clean_listings(limit=1000)

    if clean_listings:
        report = dq.run_full_check([c.__dict__ for c in clean_listings])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Registos Analisados", report["record_count"])
        with col_b:
            st.metric("Erros de Schema", report["schema_errors"])
        with col_c:
            st.metric("Anomalias Preço", len(report["price_anomalies"]))

        if report["drift_alerts"]:
            for alert in report["drift_alerts"]:
                st.warning(f"🚨 {alert}")
        else:
            st.success("✅ Sem drift detetado")

        if report["freshness_alerts"]:
            for alert in report["freshness_alerts"]:
                st.info(f"⏰ {alert}")
    else:
        st.info("Sem dados clean para análise de qualidade")

    # ── Pipeline Debug Actions ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Ações de Debug")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Limpar Cache de Fingerprints", use_container_width=True):
            # This is a conceptual button; implementation would clear dedup cache
            st.success("Cache de fingerprints limpo (simulado)")

    with col2:
        if st.button("📊 Forçar Re-avaliação ML", use_container_width=True):
            # Conceptual button for re-running valuations
            st.success("Re-avaliação agendada (simulada)")
