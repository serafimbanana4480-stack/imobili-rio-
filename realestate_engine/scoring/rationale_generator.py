"""Rationale generator explaining scores in Portuguese.

Generates rich, human-readable explanations including:
- Headline summary with emoji classification
- Valuation breakdown (estimated vs asking, savings)
- Factor-by-factor analysis
- Red flag warnings
- INE market context
- SHAP/ML insights
- Comparable properties summary
"""
from typing import Dict, List, Optional
from loguru import logger


# ── Classification mapping ─────────────────────────────────────────────
CLASSIFICATION_DISPLAY = {
    "Imperdível": {"emoji": "🔥", "cor": "#FF0000", "headline": "OPORTUNIDADE IMPERDÍVEL"},
    "Excelente": {"emoji": "⭐", "cor": "#FF6600", "headline": "OPORTUNIDADE EXCELENTE"},
    "Bom": {"emoji": "✅", "cor": "#00CC00", "headline": "BOA OFERTA"},
    "Aceitável": {"emoji": "➡️", "cor": "#999999", "headline": "OFERTA MÉDIA"},
    "Não recomendado": {"emoji": "❌", "cor": "#CC0000", "headline": "NÃO RECOMENDADO"},
}


class RationaleGenerator:
    """Generates human-readable rationale for scores in Portuguese."""

    @staticmethod
    def generate(
        scores: Dict[str, float],
        red_flags: List[str],
        listing: Optional[Dict] = None,
        valuation: Optional[Dict] = None,
    ) -> str:
        """Generate rich rationale text explaining the score."""
        listing = listing or {}
        valuation = valuation or {}

        total_score = sum(
            scores.get(k, 0) * w
            for k, w in [("discount", 0.30), ("location", 0.25),
                         ("condition", 0.15), ("liquidity", 0.15), ("freshness", 0.15)]
        )

        parts = []

        # ── 1. Headline ────────────────────────────────────────────────
        classificacao = _classify(total_score)
        display = CLASSIFICATION_DISPLAY.get(classificacao, {})
        emoji = display.get("emoji", "📍")
        headline = display.get("headline", classificacao.upper())
        parts.append(f"{emoji} {headline} — Score {total_score:.1f}/10")
        parts.append("")

        # ── 2. Valuation summary ────────────────────────────────────────
        discount_pct = valuation.get("discount")
        valor_justo = valuation.get("valor_justo")
        preco = listing.get("preco_pedido")

        if discount_pct is not None and valor_justo and preco:
            pct = discount_pct * 100
            area = listing.get("area_util_m2") or 0
            if pct > 0:
                saving = valor_justo - preco
                tipologia = listing.get("tipologia") or "Imóvel"
                freguesia = listing.get("freguesia") or ""
                parts.append(
                    f"💰 Este {tipologia} ({area:.0f}m²) em {freguesia} está "
                    f"**{pct:.0f}% abaixo** do valor de mercado estimado."
                )
                parts.append(
                    f"📊 Avaliação: {valor_justo:,.0f}€ estimado vs "
                    f"{preco:,.0f}€ pedido (poupança: {saving:,.0f}€)"
                )
            elif pct < -5:
                parts.append(
                    f"📊 Preço {abs(pct):.0f}% acima do valor de mercado estimado "
                    f"({valor_justo:,.0f}€)"
                )
            else:
                parts.append(f"📊 Preço alinhado com o mercado ({valor_justo:,.0f}€ estimado)")
            parts.append("")

        # ── 3. Factor breakdown ─────────────────────────────────────────
        parts.append("📋 **Análise por factor:**")

        # Discount
        disc = scores.get("discount", 0)
        if disc >= 8:
            parts.append(f"  ✅ Desconto: {disc:.1f}/10 — Subvalorização significativa detectada")
        elif disc >= 6:
            parts.append(f"  ✅ Desconto: {disc:.1f}/10 — Desconto moderado face ao mercado")
        elif disc >= 4:
            parts.append(f"  ➡️ Desconto: {disc:.1f}/10 — Preço próximo do valor de mercado")
        else:
            parts.append(f"  ❌ Desconto: {disc:.1f}/10 — Sem desconto ou sobrevalorizado")

        # Location
        loc = scores.get("location", 0)
        freguesia = listing.get("freguesia") or ""
        concelho = listing.get("concelho") or ""
        loc_name = f"{freguesia}, {concelho}" if freguesia else concelho
        if loc >= 8:
            parts.append(f"  ✅ Localização: {loc:.1f}/10 — {loc_name} (zona premium)")
        elif loc >= 6:
            parts.append(f"  ✅ Localização: {loc:.1f}/10 — {loc_name} (boa zona)")
        elif loc >= 4:
            parts.append(f"  ➡️ Localização: {loc:.1f}/10 — {loc_name}")
        else:
            parts.append(f"  ⬇️ Localização: {loc:.1f}/10 — {loc_name} (zona periférica)")

        # Condition
        cond = scores.get("condition", 0)
        estado = listing.get("estado") or "N/D"
        cert = listing.get("cert_energetico") or "N/D"
        ano = listing.get("ano_construcao")
        cond_detail = f"Estado: {estado}"
        if ano:
            cond_detail += f", Ano: {ano}"
        if cert != "N/D":
            cond_detail += f", Cert: {cert}"
        if cond >= 7:
            parts.append(f"  ✅ Condição: {cond:.1f}/10 — {cond_detail}")
        elif cond >= 4:
            parts.append(f"  ➡️ Condição: {cond:.1f}/10 — {cond_detail}")
        else:
            parts.append(f"  ⬇️ Condição: {cond:.1f}/10 — {cond_detail}")

        # Liquidity
        liq = scores.get("liquidity", 0)
        if liq >= 7:
            parts.append(f"  ✅ Liquidez: {liq:.1f}/10 — Fácil revenda")
        elif liq >= 4:
            parts.append(f"  ➡️ Liquidez: {liq:.1f}/10 — Liquidez média")
        else:
            parts.append(f"  ⬇️ Liquidez: {liq:.1f}/10 — Revenda pode ser difícil")

        # Freshness
        fresh = scores.get("freshness", 0)
        if fresh >= 8:
            parts.append(f"  ✅ Frescura: {fresh:.1f}/10 — Anúncio recente")
        elif fresh >= 5:
            parts.append(f"  ➡️ Frescura: {fresh:.1f}/10 — Algumas semanas no mercado")
        else:
            parts.append(f"  ⬇️ Frescura: {fresh:.1f}/10 — Anúncio antigo")

        # ── 4. Red flags ────────────────────────────────────────────────
        if red_flags:
            parts.append("")
            parts.append(f"⚠️ **Pontos de atenção ({len(red_flags)}):**")
            for flag in red_flags[:5]:
                parts.append(f"  {flag}")

        # ── 5. SHAP/XGBoost insights ───────────────────────────────────
        if valuation and valuation.get("xgboost_explanation"):
            expl = valuation["xgboost_explanation"]
            sorted_feats = sorted(expl.items(), key=lambda x: abs(x[1]), reverse=True)
            if sorted_feats:
                parts.append("")
                parts.append("🤖 **Factores ML mais influentes:**")
                for name, val in sorted_feats[:3]:
                    direction = "↑ valoriza" if val > 0 else "↓ desvaloriza"
                    readable = _feature_readable(name)
                    parts.append(f"  • {readable}: {direction} ({val:+.3f})")

        # ── 6. INE context ──────────────────────────────────────────────
        ine_m2 = listing.get("ine_preco_medio_m2")
        ine_trend = listing.get("ine_tendencia_mensal")
        preco_m2 = listing.get("preco_por_m2")
        if ine_m2 and preco_m2:
            parts.append("")
            ratio = preco_m2 / ine_m2
            if ratio < 0.85:
                ine_note = f"**abaixo** da mediana INE"
            elif ratio < 1.05:
                ine_note = f"alinhado com a mediana INE"
            else:
                ine_note = f"**acima** da mediana INE"
            parts.append(
                f"📈 INE: {preco_m2:,.0f}€/m² pedido vs {ine_m2:,.0f}€/m² mediana "
                f"({ine_note})"
            )
            if ine_trend:
                parts.append(f"   Tendência mensal: {ine_trend:+.1f}%")

        # ── 7. Confidence ───────────────────────────────────────────────
        confianca = valuation.get("confianca")
        if confianca is not None:
            parts.append("")
            if confianca >= 0.75:
                parts.append(f"🟢 Confiança da avaliação: {confianca:.0%} (alta)")
            elif confianca >= 0.50:
                parts.append(f"🟡 Confiança da avaliação: {confianca:.0%} (moderada)")
            else:
                parts.append(f"🔴 Confiança da avaliação: {confianca:.0%} (baixa — poucos dados)")

        return "\n".join(parts)

    @staticmethod
    def generate_telegram_summary(
        scores: Dict[str, float],
        red_flags: List[str],
        listing: Optional[Dict] = None,
        valuation: Optional[Dict] = None,
    ) -> str:
        """Generate compact summary for Telegram messages."""
        listing = listing or {}
        valuation = valuation or {}

        lines = []

        # Quick valuation line
        discount_pct = valuation.get("discount")
        valor_justo = valuation.get("valor_justo")
        if discount_pct is not None and valor_justo:
            pct = discount_pct * 100
            if pct > 0:
                lines.append(f"💰 {pct:.0f}% abaixo do mercado (est. {valor_justo:,.0f}€)")
            elif pct < -5:
                lines.append(f"⚠️ {abs(pct):.0f}% acima do mercado")

        # Top 2 factors
        best_factor = max(scores.items(), key=lambda x: x[1]) if scores else None
        if best_factor:
            lines.append(f"⭐ Melhor: {_factor_pt(best_factor[0])} ({best_factor[1]:.1f}/10)")

        # Red flag count
        if red_flags:
            lines.append(f"⚠️ {len(red_flags)} alerta(s)")

        return " | ".join(lines) if lines else "Análise indisponível"


def _classify(score: float) -> str:
    if score >= 8.5:
        return "Imperdível"
    elif score >= 7.0:
        return "Excelente"
    elif score >= 5.5:
        return "Bom"
    elif score >= 4.0:
        return "Aceitável"
    else:
        return "Não recomendado"


def _factor_pt(name: str) -> str:
    """Translate factor name to Portuguese."""
    return {
        "discount": "Desconto",
        "location": "Localização",
        "condition": "Condição",
        "liquidity": "Liquidez",
        "freshness": "Frescura",
    }.get(name, name.title())


def _feature_readable(name: str) -> str:
    """Convert SHAP feature name to readable Portuguese."""
    return {
        "log_area": "Área",
        "quartos": "Quartos",
        "casas_banho": "Casas de banho",
        "andar": "Andar",
        "sqrt_idade": "Idade do edifício",
        "cert_score": "Certificado energético",
        "estado_score": "Estado de conservação",
        "lat": "Latitude",
        "lon": "Longitude",
        "dist_metro_m": "Distância ao metro",
        "dist_escola_m": "Distância a escola",
        "tem_garagem": "Garagem",
        "tem_piscina": "Piscina",
        "tem_vista_premium": "Vista mar/rio",
        "freguesia_effect": "Efeito da freguesia",
        "freg_median_m2": "Mediana do bairro",
    }.get(name, name)
