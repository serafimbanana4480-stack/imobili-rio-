"""System status page for dashboard."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import psutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.monitoring.health_checks import HealthCheck
from realestate_engine.dashboard.utils.theme import (
    is_dark_mode,
    TEXT_COLOR_MUTED_LIGHT,
    TEXT_COLOR_MUTED_DARK,
)


def render_system():
    """Render system status page."""
    st.title(" Estado do Sistema")
    st.markdown("*Monitorização do estado e saúde do sistema*")

    repo = DatabaseRepository()

    #  System Metrics 
    st.markdown("###  Métricas do Sistema")

    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        cpu_pct = process.cpu_percent(interval=0.1)
        threads = process.num_threads()
    except Exception:
        mem_info = None
        cpu_pct = 0
        threads = 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if mem_info:
            mem_mb = mem_info.rss / (1024 * 1024)
            st.metric(" Memória", f"{mem_mb:.0f} MB")
        else:
            st.metric(" Memória", "N/A")
    with col2:
        st.metric(" CPU", f"{cpu_pct:.1f}%")
    with col3:
        st.metric(" Threads", f"{threads}")
    with col4:
        st.metric(" Uptime", datetime.now().strftime("%H:%M:%S"))

    #  Health Checks 
    st.markdown("---")
    st.markdown("###  Verificações de Saúde")

    hc = HealthCheck()
    checks = hc.get_all_checks()

    def status_badge(status):
        emojis = {"healthy": "", "degraded": "", "warning": "", "unhealthy": "", "unknown": ""}
        return f"{emojis.get(status, '')} {status.upper()}"

    # Show overall first
    overall = checks.get("overall", "unknown")
    st.markdown(f"**Sistema:** {status_badge(overall)}")

    # Detailed health table
    health_items = [
        (" Base de Dados", "database"),
        (" Scraping", "scraping"),
        ("⏰ Scheduler", "scheduler"),
        (" APIs Externas", "external_apis"),
        (" Disco", "disk_space"),
        (" Memória", "memory"),
        (" Redis (opcional)", "redis"),
    ]

    for label, key in health_items:
        check = checks.get(key, {})
        status = check.get("status", "unknown")
        note = check.get("note", check.get("error", ""))
        fix = check.get("fix", "")

        if status in ("healthy",):
            continue  # Don't clutter with healthy items

        with st.container():
            col_status, col_detail = st.columns([1, 3])
            with col_status:
                st.markdown(f"**{label}**")
                st.markdown(status_badge(status))
            with col_detail:
                if note:
                    st.markdown(f" **Motivo:** {note}")
                if fix:
                    st.markdown(f" **Como resolver:** {fix}")

    # Show healthy components in compact form
    healthy_items = [label for label, key in health_items if checks.get(key, {}).get("status") == "healthy"]
    if healthy_items:
        st.caption(f" Saudáveis: {', '.join(healthy_items)}")

    #  Portal Status 
    st.markdown("---")
    st.markdown("###  Estado dos Portais")

    try:
        raw_listings = repo.get_raw_listings(limit=100000)
        portal_counts = {}
        for rl in raw_listings:
            p = rl.source_portal or "desconhecido"
            portal_counts[p] = portal_counts.get(p, 0) + 1

        portal_info = [
            ("imovirtual", "Imovirtual", "Next.js __NEXT_DATA__ — funciona sem browser"),
            ("idealista", "Idealista", "Requer proxy + browser (anti-bot alto)"),
            ("casa_sapo", "Casa Sapo", "Direct fetch / JSON-LD — sem browser"),
            ("era", "ERA", "Nodriver spider — requer browser"),
            ("remax", "RE/MAX", "Direct fetch via sitemap — sem browser"),
            ("supercasa", "SuperCasa", "Nodriver spider — requer browser"),
            ("century21", "Century21", "Nodriver spider — requer browser"),
            ("olx", "OLX", "Nodriver spider — requer browser"),
        ]

        pcols = st.columns(4)
        for i, (key, name, tech) in enumerate(portal_info):
            with pcols[i % 4]:
                count = portal_counts.get(key, 0)
                has_data = count > 0
                emoji = "" if has_data else ""
                muted_color = TEXT_COLOR_MUTED_DARK if is_dark_mode() else TEXT_COLOR_MUTED_LIGHT
                st.markdown(f"""
                <div class="re-card" style="border-left:3px solid {'#10B981' if has_data else '#EF4444'};">
                    <div style="font-weight:600;">{emoji} {name}</div>
                    <div style="font-size:0.85em;color:{muted_color};">{count:,} anúncios</div>
                    <div style="font-size:0.75em;color:{muted_color};">{tech}</div>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Dados de portais não disponíveis: {e}")

    #  Job Execution History 
    st.markdown("---")
    st.markdown("###  Histórico de Execuções")

    job_names = ["spider_manager", "pipeline_etl", "valuation_engine", "scoring_engine", "notification_engine"]

    job_data = []
    for job_name in job_names:
        executions = repo.get_recent_job_executions(job_name, limit=5)
        for exec in executions:
            job_data.append({
                "Job": job_name.replace("_", " ").title(),
                "Início": exec.started_at.strftime("%Y-%m-%d %H:%M") if exec.started_at else "",
                "Estado": exec.status.upper(),
                "Registos": exec.records_processed or 0,
                "Duração (s)": round((exec.finished_at - exec.started_at).total_seconds(), 1) if exec.finished_at and exec.started_at else None,
            })

    if job_data:
        df = pd.DataFrame(job_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Sem histórico de execuções. Executa o pipeline para começar.")

    #  Pipeline Actions 
    st.markdown("---")
    st.markdown("###  Ações do Pipeline")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(" Executar Scraping", type="primary"):
            st.session_state['page'] = " Scraping"
            st.session_state['scraping_running'] = True
            st.session_state['scraping_message'] = "Iniciando scraping..."
            st.rerun()
    with col2:
        if st.button(" Iniciar Pipeline Completo", type="primary"):
            st.session_state['page'] = " Sistema"
            st.session_state['system_page'] = " Pipeline"
            st.rerun()
    with col3:
        if st.button(" Atualizar Dados"):
            st.rerun()

    #  Disk & DB Info 
    st.markdown("---")
    st.markdown("###  Informações do Disco")

    try:
        disk = psutil.disk_usage('/')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"{disk.total / (1024**3):.1f} GB")
        with col2:
            st.metric("Usado", f"{disk.used / (1024**3):.1f} GB")
        with col3:
            pct = disk.percent
            delta = " Pouco espaço" if pct > 85 else None
            st.metric("Livre", f"{disk.free / (1024**3):.1f} GB", delta=delta)
    except Exception:
        st.info("Informação de disco não disponível")

