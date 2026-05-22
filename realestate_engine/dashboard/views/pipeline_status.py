"""Real-time Pipeline Status dashboard view.

Shows:
- Current pipeline phase (Scraping / ETL / Valuation / Scoring / Idle)
- Last execution timestamps per phase
- Success/failure counts
- Throughput (listings/minute)
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from realestate_engine.database.repository import DatabaseRepository


def render_pipeline_status():
    """Render real-time pipeline status page."""
    st.title(" Pipeline Status")
    st.markdown("*Monitorização de todas as fases do pipeline de dados*")

    repo = DatabaseRepository()

    #  Phase Cards 
    st.markdown("###  Fases do Pipeline")
    col1, col2, col3, col4, col5 = st.columns(5)

    phases = [
        (" Scraping", "spider_manager", "#3B82F6"),
        (" ETL", "pipeline_etl", "#8B5CF6"),
        (" Valuation", "valuation_engine", "#10B981"),
        (" Scoring", "scoring_engine", "#F59E0B"),
        (" Notificações", "notification_engine", "#EF4444"),
    ]

    for (label, job_name, color), col in zip(phases, [col1, col2, col3, col4, col5]):
        with col:
            executions = repo.get_recent_job_executions(job_name, limit=1)
            if executions:
                last = executions[0]
                status_emoji = "" if last.status == "success" else "" if last.status == "failed" else ""
                st.markdown(f"""
                <div class="re-card" style="border-left:3px solid {color};">
                    <div style="font-weight:600;font-size:0.9em;margin-bottom:4px;">{label}</div>
                    <div style="font-size:1.1em;font-weight:700;">{status_emoji} {last.status.upper()}</div>
                </div>
                """, unsafe_allow_html=True)
                if last.finished_at:
                    ago = datetime.now() - last.finished_at.replace(tzinfo=None)
                    if ago.total_seconds() < 3600:
                        st.caption(f"⏱ {ago.total_seconds()/60:.0f} min atrás")
                    else:
                        st.caption(f"⏱ {ago.total_seconds()/3600:.0f}h atrás")
            else:
                st.markdown(f"""
                <div class="re-card" style="border-left:3px solid {color};">
                    <div style="font-weight:600;font-size:0.9em;margin-bottom:4px;">{label}</div>
                    <div style="font-size:1.1em;font-weight:700;"> IDLE</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("Sem execuções")

    #  Execution History 
    st.markdown("---")
    st.markdown("###  Histórico de Execuções")

    job_names = ["spider_manager", "pipeline_etl", "valuation_engine", "scoring_engine", "notification_engine"]
    all_jobs = []
    for job_name in job_names:
        executions = repo.get_recent_job_executions(job_name, limit=10)
        for exec in executions:
            all_jobs.append({
                "Job": job_name.replace("_", " ").title(),
                "Início": exec.started_at.strftime("%Y-%m-%d %H:%M:%S") if exec.started_at else "",
                "Fim": exec.finished_at.strftime("%Y-%m-%d %H:%M:%S") if exec.finished_at else "",
                "Estado": exec.status.upper(),
                "Registos": exec.records_processed or 0,
                "Duração (s)": round((exec.finished_at - exec.started_at).total_seconds(), 1) if exec.finished_at and exec.started_at else None,
            })

    if all_jobs:
        df_jobs = pd.DataFrame(all_jobs)
        st.dataframe(df_jobs.sort_values("Início", ascending=False), hide_index=True, use_container_width=True)
    else:
        st.info("Sem histórico de execuções. Executa o pipeline para começar.")

    #  Throughput Metrics 
    st.markdown("---")
    st.markdown("###  Throughput & Performance")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        raw_count = len(repo.get_raw_listings(limit=100000))
        st.metric("Total Raw Listings", f"{raw_count:,}".replace(",", "."))

    with col_b:
        clean_count = len(repo.get_clean_listings(limit=100000))
        st.metric("Total Clean Listings", f"{clean_count:,}".replace(",", "."))

    with col_c:
        score_count = len(repo.get_top_scores(min_score=0.0, limit=100000))
        st.metric("Total Scored", f"{score_count:,}".replace(",", "."))

    # Pipeline throughput chart
    if all_jobs:
        df_t = pd.DataFrame(all_jobs)
        df_t = df_t[df_t["Estado"] == "SUCCESS"]
        if not df_t.empty and "Duração (s)" in df_t.columns:
            df_t = df_t.dropna(subset=["Duração (s)"])
            if not df_t.empty:
                import plotly.express as px
                fig = px.bar(df_t, x="Job", y="Duração (s)", color="Job",
                             title="Duração da Última Execução por Job (s)")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    #  Pipeline Actions 
    st.markdown("---")
    st.markdown("###  Ações Rápidas")

    st.info(
        "ℹ O pipeline corre automaticamente em loop pelo Orchestrator (24/7). "
        "Para execução manual com feedback ao vivo (logs, progresso por portal, "
        "novos vs duplicados), usa a página ** Scraping**."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Ir para Scraping (execução manual)", type="primary", width="stretch"):
            st.session_state['page'] = " Sistema"
            st.session_state['system_page'] = " Scraping"
            st.rerun()
    with col2:
        if st.button(" Atualizar Dados", width="stretch"):
            st.rerun()

