"""Score audit view — distribuition, sub-score breakdown, hard-cap impact analysis.

Surfaces:
- Score distribution histogram with classification thresholds
- Sub-score (discount/location/condition/amenities/liquidity/freshness) box plots
- Hard-cap impact: how many listings are capped by missing photos/coords/red-flags
- Top-10 / Bottom-10 with rationale
"""
from __future__ import annotations

import statistics
from collections import Counter

import pandas as pd
import streamlit as st

from realestate_engine.dashboard.utils.theme import apply_theme
from realestate_engine.database.models import CleanListing, Score
from realestate_engine.database.repository import DatabaseRepository


def render_score_audit():
    st.title("🏆 Auditoria Executiva de Score & Valuation")
    st.caption("Visão comercial da distribuição de oportunidades, credibilidade do valuation e impacto dos hard-caps")

    repo = DatabaseRepository()
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    with repo.Session() as session:
        scores = session.execute(
            select(Score)
            .options(
                selectinload(Score.listing)
                .selectinload(CleanListing.valuations)
            )
        ).scalars().all()

    if not scores:
        st.warning("Sem scores na BD. Executa o pipeline primeiro.")
        return

    vals = [s.score_total for s in scores if s.score_total is not None]
    if not vals:
        st.warning("Scores existem mas sem score_total preenchido.")
        return

    # ── Executive summary ────────────────────────────────────────────────
    valuations = []
    listings_with_valuation = []
    for s in scores:
        l = getattr(s, "listing", None)
        if not l or not getattr(l, "valuations", None):
            continue
        val = l.valuations[0]
        if val and val.valor_justo and l.preco_pedido and l.preco_pedido > 0:
            valuations.append(val.valor_justo)
            listings_with_valuation.append((l, s, val))

    score_avg = statistics.mean(vals)
    score_median = statistics.median(vals)
    score_max = max(vals)
    score_min = min(vals)
    excellent_count = sum(1 for v in vals if v >= 7.5)
    imperdivel_count = sum(1 for v in vals if v >= 9.0)
    cases_above_fair_value = sum(1 for l, s, val in listings_with_valuation if val.valor_justo < l.preco_pedido)
    cases_with_positive_gap = sum(1 for l, s, val in listings_with_valuation if val.valor_justo > l.preco_pedido)

    valuation_widths = []
    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    for l, s, val in listings_with_valuation:
        if val.ci_lower is not None and val.ci_upper is not None and val.valor_justo:
            valuation_widths.append((val.ci_upper - val.ci_lower) / val.valor_justo)
        if val.confianca is not None:
            if val.confianca >= 0.75:
                high_confidence += 1
            elif val.confianca >= 0.50:
                medium_confidence += 1
            else:
                low_confidence += 1

    total_with_valuation = len(listings_with_valuation)
    robust_share = (high_confidence / total_with_valuation) if total_with_valuation else 0
    cautious_share = (low_confidence / total_with_valuation) if total_with_valuation else 0
    avg_width = statistics.mean(valuation_widths) if valuation_widths else 0.0
    executive_readout = (
        "Base comercial madura e com valuation defensável." if robust_share >= 0.6 and avg_width <= 0.25 else
        "Base comercial utilizável, mas ainda sensível à qualidade dos dados e dos comparáveis." if cautious_share < 0.35 else
        "Base comercial com incerteza relevante; reforçar dados antes de escalar a tese de investimento."
    )

    # ── KPI row ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total avaliados", f"{len(scores):,}".replace(",", "."))
    c2.metric("Score médio", f"{score_avg:.2f}")
    c3.metric("Score mediano", f"{score_median:.2f}")
    c4.metric("Casos fortes (≥7.5)", f"{excellent_count:,}".replace(",", "."))
    c5.metric("Casos premium (≥9.0)", f"{imperdivel_count:,}".replace(",", "."))

    c6, c7, c8 = st.columns(3)
    with c6:
        st.metric("Casos com margem positiva", f"{cases_with_positive_gap:,}".replace(",", "."))
    with c7:
        st.metric("Casos acima do valor justo", f"{cases_above_fair_value:,}".replace(",", "."))
    with c8:
        st.metric("Faixa observada do score", f"{score_min:.2f} → {score_max:.2f}")

    if listings_with_valuation:
        c9, c10, c11 = st.columns(3)
        with c9:
            st.metric("Valuation robusto", high_confidence)
        with c10:
            st.metric("Valuation intermédio", medium_confidence)
        with c11:
            st.metric("Valuation cauteloso", low_confidence)
        st.caption(
            f"Intervalo médio do valuation: {avg_width*100:.1f}% do valor estimado"
            if valuation_widths else "Intervalo médio do valuation indisponível"
        )

    st.info(
        "Esta página resume se o motor está a gerar margem defensável, valuation credível e distribuição saudável."
    )
    st.success(executive_readout)

    # ── Classification distribution ────────────────────────────────────────
    st.markdown("### Distribuição por Classificação")
    cls_counts = Counter(s.classificacao for s in scores if s.classificacao)
    df_cls = pd.DataFrame(
        sorted(cls_counts.items(), key=lambda kv: -kv[1]),
        columns=["Classificação", "Total"],
    )
    df_cls["%"] = (df_cls["Total"] / df_cls["Total"].sum() * 100).round(1)
    st.dataframe(df_cls, use_container_width=True, hide_index=True)

    # ── Histogram with classification thresholds ───────────────────────────
    try:
        import plotly.express as px
        import plotly.graph_objects as go

        st.markdown("### Histograma de Score Total")
        fig = px.histogram(
            x=vals, nbins=50,
            labels={"x": "Score (0-10)", "y": "Nº de listings"},
            color_discrete_sequence=["#3B82F6"],
        )
        # Threshold markers per WeightedScoreCalculator.CLASSIFICATIONS
        thresholds = [
            (3.0, "Abaixo média", "#94A3B8"),
            (4.5, "Aceitável", "#F59E0B"),
            (6.0, "Bom", "#10B981"),
            (7.5, "Excelente", "#3B82F6"),
            (9.0, "Imperdível", "#EF4444"),
        ]
        for threshold, label, color in thresholds:
            fig.add_vline(x=threshold, line_dash="dash", line_color=color,
                          annotation_text=f"{label} ≥{threshold}",
                          annotation_position="top")
        apply_theme(fig, height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # ── Sub-score box plot ─────────────────────────────────────────────
        st.markdown("### Sub-scores (mediana, IQR, outliers)")
        sub_data = []
        for s in scores:
            for field, label in [
                ("score_discount", "Desconto"),
                ("score_location", "Localização"),
                ("score_condition", "Condição"),
                ("score_liquidity", "Liquidez"),
                ("score_freshness", "Frescura"),
            ]:
                v = getattr(s, field, None)
                if v is not None:
                    sub_data.append({"Sub-score": label, "Valor": v})
        sub_df = pd.DataFrame(sub_data)
        if not sub_df.empty:
            fig2 = px.box(sub_df, x="Sub-score", y="Valor",
                          color_discrete_sequence=["#10B981"])
            apply_theme(fig2, height=360, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.info("Instala plotly para ver gráficos.")

    # ── Hard-cap impact analysis ───────────────────────────────────────────
    st.markdown("### 🚫 Impacto das Hard-Caps")
    st.caption(
        "O scoring engine impõe tetos máximos quando faltam dados críticos. "
        "Aqui vemos quantas oportunidades são travadas por qualidade de dados e não por mérito comercial."
    )

    with repo.Session() as session:
        listings = session.execute(select(CleanListing)).scalars().all()

    no_photos = sum(1 for l in listings if not l.num_fotos)
    no_coords = sum(1 for l in listings if l.lat is None or l.lon is None)
    total = len(listings)

    cap_df = pd.DataFrame([
        {
            "Hard-cap": "Sem fotos → max 5.0",
            "Listings afetados": no_photos,
            "% do total": f"{(no_photos / total * 100) if total else 0:.1f}%",
        },
        {
            "Hard-cap": "Sem coordenadas → max 6.0",
            "Listings afetados": no_coords,
            "% do total": f"{(no_coords / total * 100) if total else 0:.1f}%",
        },
        {
            "Hard-cap": "Score >= 9.0 sem critérios Imperdível → cap 8.99",
            "Listings afetados": sum(1 for s in scores if s.score_total and s.score_total >= 9.0),
            "% do total": "(ativo após scoring)",
        },
    ])
    st.dataframe(cap_df, use_container_width=True, hide_index=True)

    st.markdown("### 📐 Leitura Comercial do Valuation")
    if listings_with_valuation:
        total_with_val = len(listings_with_valuation)
        avg_discount = statistics.mean(
            ((val.valor_justo - l.preco_pedido) / l.preco_pedido) * 100
            for l, s, val in listings_with_valuation
            if l.preco_pedido > 0 and val.valor_justo is not None
        )
        median_discount = statistics.median(
            [((val.valor_justo - l.preco_pedido) / l.preco_pedido) * 100 for l, s, val in listings_with_valuation if l.preco_pedido > 0]
        )
        ci_spread = None
        ci_items = []
        for l, s, val in listings_with_valuation:
            if getattr(val, "ci_lower", None) and getattr(val, "ci_upper", None) and val.valor_justo:
                spread = (val.ci_upper - val.ci_lower) / val.valor_justo if val.valor_justo else None
                if spread is not None:
                    ci_items.append(spread)
        if ci_items:
            ci_spread = statistics.mean(ci_items)

        c9, c10, c11 = st.columns(3)
        with c9:
            st.metric("Desconto médio implícito", f"{avg_discount:.1f}%")
        with c10:
            st.metric("Desconto mediano implícito", f"{median_discount:.1f}%")
        with c11:
            st.metric("Cobertura com valuation", f"{total_with_val:,}".replace(",", "."))

        if ci_spread is not None:
            st.caption(f"Spread médio do intervalo de confiança: {ci_spread*100:.1f}% do valor estimado")

        if high_confidence >= medium_confidence and high_confidence >= low_confidence:
            st.success("Leitura comercial: a maior parte dos valuations está numa zona robusta para decisão.")
        elif low_confidence > high_confidence:
            st.warning("Leitura comercial: há demasiada incerteza no valuation; convém reforçar dados e comparáveis.")
        else:
            st.info("Leitura comercial: o valuation é utilizável, mas ainda sensível à qualidade dos dados.")
    else:
        st.info("Ainda não há listings suficientes com valuation para calcular métricas comerciais robustas.")

    if max(vals) < 8.0:
        st.warning(
            f"⚠️ Score máximo atual = **{max(vals):.2f}**. Nenhum listing atinge 'Imperdível' (≥9.0). "
            "Causa provável: combinação de hard-caps (fotos + coords + red flags) "
            "está a comprimir a distribuição."
        )

    # ── Top / Bottom outliers ──────────────────────────────────────────────
    st.markdown("### 🥇 Top 10 Scores")
    top10 = sorted(scores, key=lambda s: s.score_total or 0, reverse=True)[:10]
    top_df = pd.DataFrame([
        {
            "Score": s.score_total,
            "Classificação": s.classificacao,
            "Desconto": s.score_discount,
            "Localização": s.score_location,
            "Condição": s.score_condition,
            "Liquidez": s.score_liquidity,
            "Listing ID": s.listing_id,
        }
        for s in top10
    ])
    st.dataframe(top_df, use_container_width=True, hide_index=True)

    st.markdown("### 🚨 Bottom 10 Scores (menor)")
    bottom10 = sorted(scores, key=lambda s: s.score_total or 0)[:10]
    bot_df = pd.DataFrame([
        {
            "Score": s.score_total,
            "Classificação": s.classificacao,
            "Desconto": s.score_discount,
            "Localização": s.score_location,
            "Condição": s.score_condition,
            "Liquidez": s.score_liquidity,
            "Listing ID": s.listing_id,
        }
        for s in bottom10
    ])
    st.dataframe(bot_df, use_container_width=True, hide_index=True)

    # ── Documentation ──────────────────────────────────────────────────────
    with st.expander("📚 Como funciona o scoring", expanded=False):
        st.markdown(
            """
        **Pesos (defaults):**

        | Fator | Peso | O que mede |
        |---|---|---|
        | Desconto | 20% | Quão abaixo do valor justo o preço está |
        | Localização | 25% | Freguesia, distância a metro/escolas/comércio, tendência INE |
        | Condição | 15% | Estado, ano de construção, certificado, qualidade de fotos |
        | Amenidades | 15% | Garagem, AC, elevador, piscina, equipamento |
        | Liquidez | 15% | €/m² vs INE, área e tipologia procuradas |
        | Frescura | 10% | Idade do anúncio (mais fresco = melhor) |

        **Hard-caps (impostos depois do score ponderado):**

        - Sem fotos → score máximo **5.0**
        - Sem coordenadas (lat/lon) → score máximo **6.0**
        - Qualquer red flag → score máximo **8.0**
        - Score ≥9.0 mas sem critérios estritos → cap a **8.99**

        **Imperdível (≥9.0) requer TODAS:**

        1. Score ponderado ≥ 9.0
        2. Desconto ≥ 15% face ao valor justo
        3. **Zero** red flags

        **Diagnóstico atual:**
        - Score máximo observado é **{maxv:.2f}** — nenhum atinge Imperdível.
        - Isto indica que a combinação de hard-caps + critérios estritos está a comprimir a distribuição.
        - Para abrir a curva: melhorar geocoding (reduz cap dos 6.0) e completude de fotos.
            """.format(maxv=max(vals))
        )
