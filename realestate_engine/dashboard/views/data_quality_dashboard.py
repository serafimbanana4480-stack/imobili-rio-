"""Data Quality & Drift Detection dashboard view.

Shows:
- % dados válidos por camada
- Nº duplicados detectados
- Nº erros por categoria
- Alertas de drift
- Anomalias de preço
- Freshness dos dados
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.monitoring.data_quality import DataQualityEngine


def render_data_quality():
    """Render data quality monitoring dashboard."""
    st.title("📊 Qualidade de Dados & Drift")
    st.markdown("*Validação contínua e deteção de anomalias em todas as camadas*")

    repo = DatabaseRepository()
    dq = DataQualityEngine()

    # ── Load data ──────────────────────────────────────────────────────────
    clean_listings = repo.get_clean_listings(limit=5000)
    raw_listings = repo.get_raw_listings(limit=5000)
    scores = repo.get_top_scores(min_score=0.0, limit=5000)

    if not clean_listings:
        st.warning("⚠️ Sem dados clean na base de dados. Execute o pipeline primeiro.")
        return

    # ── Top KPIs ─────────────────────────────────────────────────────────
    st.markdown("### 📈 Métricas de Qualidade")
    col1, col2, col3, col4 = st.columns(4)

    # Calculate validity rate
    schema_errors_total = 0
    for c in clean_listings:
        schema_errors_total += len(dq.validate_schema(c.__dict__))

    total_fields = len(clean_listings) * len(dq.CLEAN_LISTING_SCHEMA)
    validity_rate = max(0, 100 - (schema_errors_total / total_fields * 100)) if total_fields > 0 else 100

    with col1:
        st.metric("✅ Dados Válidos", f"{validity_rate:.1f}%")

    with col2:
        raw_count = len(raw_listings)
        clean_count = len(clean_listings)
        loss_pct = (1 - clean_count / raw_count) * 100 if raw_count > 0 else 0
        st.metric("📉 Perda Pipeline", f"{loss_pct:.1f}%", delta=f"-{raw_count - clean_count}")

    with col3:
        # Duplicates: raw count vs unique source_ids
        raw_ids = [r.source_id for r in raw_listings]
        duplicates = len(raw_ids) - len(set(raw_ids))
        st.metric("🔄 Duplicados", duplicates)

    with col4:
        stale_count = 0
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=48)
        for c in clean_listings:
            ts = c.scrape_timestamp
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))
                    if dt.replace(tzinfo=None) < cutoff:
                        stale_count += 1
                except Exception:
                    stale_count += 1
            else:
                stale_count += 1
        st.metric("⏰ Stale (>48h)", stale_count)

    # ── Price Anomalies ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💰 Anomalias de Preço (IQR)")

    anomalies = dq.detect_price_anomalies([c.__dict__ for c in clean_listings])
    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        st.warning(f"⚠️ {len(anomalies)} anomalias de preço detetadas")
        st.dataframe(df_anom[["source_id", "preco_pedido", "threshold_lower", "threshold_upper"]],
                     hide_index=True, use_container_width=True)
    else:
        st.success("✅ Sem anomalias de preço detetadas")

    # ── Distribution Stats ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Estatísticas de Distribuição")

    stats = dq.calculate_batch_stats([c.__dict__ for c in clean_listings])
    if stats:
        stats_data = []
        for field, vals in stats.items():
            stats_data.append({
                "Campo": field,
                "Count": vals["count"],
                "Média": vals["mean"],
                "Mediana": vals["median"],
                "Std": vals["std"],
                "Min": vals["min"],
                "Max": vals["max"],
            })
        st.dataframe(pd.DataFrame(stats_data), hide_index=True, use_container_width=True)
    else:
        st.info("Sem estatísticas disponíveis")

    # ── Drift Detection ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚨 Alertas de Drift")

    drift_alerts = dq.detect_drift(stats)
    if drift_alerts:
        for alert in drift_alerts:
            st.error(alert)
    else:
        st.success("✅ Sem drift detetado na distribuição atual")

    # ── Layer Validation ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Validação por Camada")

    from realestate_engine.pipeline_validators import ETLValidator, ValuationValidator, ScoringValidator

    # ETL validation samples
    etl_errors = []
    for c in clean_listings[:50]:
        etl_errors.extend(ETLValidator.validate(c.__dict__))
    if etl_errors:
        with st.expander(f"ETL: {len(etl_errors)} erros (amostra 50)"):
            for e in etl_errors[:20]:
                st.error(e)
    else:
        st.success("✅ ETL: sem erros na amostra")

    # Scoring validation
    score_errors = []
    for s in scores[:50]:
        if s.listing:
            score_errors.extend(ScoringValidator.validate(s.__dict__, s.listing.__dict__))
    if score_errors:
        with st.expander(f"Scoring: {len(score_errors)} erros (amostra 50)"):
            for e in score_errors[:20]:
                st.warning(e)
    else:
        st.success("✅ Scoring: sem erros na amostra")
