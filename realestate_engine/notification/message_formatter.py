"""Message formatter for Telegram notifications.

Enhanced with:
- Full Portuguese language
- Rich formatting with markdown
- Valuation breakdown with savings
- Red flag severity display
- Compact and detailed format variants
- Price history alerts
"""
from typing import Dict, Optional
from loguru import logger


class MessageFormatter:
    """Formats opportunity notifications for Telegram."""

    # Emoji mapping for classification
    EMOJI_MAP = {
        "Imperdível": "🔥",
        "Excelente": "⭐",
        "Bom": "✅",
        "Aceitável": "➡️",
        "Abaixo da média": "⬇️",
        "Não recomendado": "❌",
    }

    @classmethod
    def format_opportunity(cls, opportunity: Dict) -> str:
        """Format a single opportunity as rich Telegram message."""
        listing = opportunity["listing"]
        score = opportunity["score"]

        emoji = cls.EMOJI_MAP.get(score.classificacao, "📍")

        # ── Header ──────────────────────────────────────────────────────
        lines = [
            f"{emoji} *{score.classificacao}* — Score {score.score_total:.1f}/10",
            "",
        ]

        # ── Property info ───────────────────────────────────────────────
        titulo = listing.titulo or "Imóvel"
        lines.append(f"🏠 *{titulo}*")

        # Price line
        price = f"{listing.preco_pedido:,.0f}€".replace(",", ".")
        price_m2 = ""
        if listing.preco_por_m2:
            price_m2 = f" ({listing.preco_por_m2:,.0f}€/m²)".replace(",", ".")
        lines.append(f"💵 {price}{price_m2}")

        # Property details
        area = f"{listing.area_util_m2:.0f}m²" if listing.area_util_m2 else "N/D"
        quartos = listing.quartos or 0
        wc = listing.casas_banho or 0
        tipologia = listing.tipologia or ""
        details = f"📐 {area} | 🛏️ {quartos}q | 🚿 {wc}wc"
        if tipologia:
            details += f" | {tipologia}"
        lines.append(details)

        # Location
        freg = listing.freguesia or ""
        conc = listing.concelho or ""
        location = f"{freg}, {conc}".strip(", ")
        if location:
            lines.append(f"📍 {location}")

        # Condition
        estado = listing.estado
        cert = listing.cert_energetico
        ano = listing.ano_construcao
        condition_parts = []
        if estado:
            condition_parts.append(estado.title())
        if ano:
            condition_parts.append(f"Ano: {ano}")
        if cert:
            condition_parts.append(f"Cert: {cert}")
        if condition_parts:
            lines.append(f"🔧 {' | '.join(condition_parts)}")

        lines.append("")

        # ── Valuation info ──────────────────────────────────────────────
        if listing.valuations:
            val = listing.valuations[0]
            if val.discount is not None:
                pct = val.discount * 100
                if pct > 0:
                    saving = val.valor_justo - listing.preco_pedido
                    saving_str = f"{saving:,.0f}€".replace(",", ".")
                    valor_str = f"{val.valor_justo:,.0f}€".replace(",", ".")
                    lines.append(f"💰 *{pct:.0f}% abaixo do mercado*")
                    lines.append(f"📊 Valor estimado: {valor_str} (poupança: {saving_str})")
                elif pct < -5:
                    lines.append(f"⚠️ {abs(pct):.0f}% acima do valor de mercado")
                else:
                    lines.append(f"📊 Preço alinhado com o mercado")

            # Confidence
            if val.confianca is not None:
                conf_pct = val.confianca * 100
                if conf_pct >= 75:
                    lines.append(f"🟢 Confiança: {conf_pct:.0f}%")
                elif conf_pct >= 50:
                    lines.append(f"🟡 Confiança: {conf_pct:.0f}%")
                else:
                    lines.append(f"🔴 Confiança: {conf_pct:.0f}%")

            lines.append("")

        # ── Score breakdown ─────────────────────────────────────────────
        lines.append("📋 *Análise:*")
        lines.append(f"  Desconto: {cls._bar(score.score_discount)} {score.score_discount:.1f}")
        lines.append(f"  Localização: {cls._bar(score.score_location)} {score.score_location:.1f}")
        lines.append(f"  Condição: {cls._bar(score.score_condition)} {score.score_condition:.1f}")
        lines.append(f"  Liquidez: {cls._bar(score.score_liquidity)} {score.score_liquidity:.1f}")
        lines.append(f"  Frescura: {cls._bar(score.score_freshness)} {score.score_freshness:.1f}")

        # ── Red flags ───────────────────────────────────────────────────
        if score.red_flags:
            lines.append("")
            for flag in score.red_flags[:3]:
                lines.append(f"{flag}")

        # ── Link ────────────────────────────────────────────────────────
        lines.append("")
        lines.append(f"🔗 [Ver anúncio]({listing.source_url})")

        message = "\n".join(lines)
        return message[:4096]  # Telegram message limit

    @staticmethod
    def _bar(score: float) -> str:
        """Generate a simple visual bar for score."""
        if score is None:
            return "░░░░░"
        filled = round(score / 2)  # 0-5 blocks
        filled = max(0, min(5, filled))  # Clamp to 0-5
        return "█" * filled + "░" * (5 - filled)

    @classmethod
    def format_daily_summary(cls, opportunities: list, total_listings: int, total_new: int) -> str:
        """Format a daily summary message."""
        lines = [
            "📊 *Resumo Diário — Real Estate Engine*",
            "",
            f"🏠 Total anúncios tracked: {total_listings:,}".replace(",", "."),
            f"🆕 Novos hoje: {total_new}",
            f"⭐ Oportunidades detectadas: {len(opportunities)}",
            "",
        ]

        if opportunities:
            lines.append("*Top 5 oportunidades:*")
            for i, opp in enumerate(opportunities[:5], 1):
                listing = opp["listing"]
                score = opp["score"]
                emoji = cls.EMOJI_MAP.get(score.classificacao, "📍")
                price = f"{listing.preco_pedido:,.0f}€".replace(",", ".")
                freg = listing.freguesia or ""
                lines.append(
                    f"{i}. {emoji} {score.score_total:.1f}/10 — "
                    f"{price} — {freg}"
                )
        else:
            lines.append("_Nenhuma oportunidade acima do threshold hoje._")

        return "\n".join(lines)

    @classmethod
    def format_price_drop_alert(cls, listing, old_price: float, new_price: float) -> str:
        """Format a price drop alert."""
        drop_pct = (old_price - new_price) / old_price * 100
        drop_abs = old_price - new_price

        return (
            f"📉 *DESCIDA DE PREÇO*\n\n"
            f"🏠 {listing.titulo or 'Imóvel'}\n"
            f"📍 {listing.freguesia or ''}, {listing.concelho or ''}\n\n"
            f"💵 ~~{old_price:,.0f}€~~ → *{new_price:,.0f}€*\n"
            f"📊 Descida: {drop_pct:.1f}% ({drop_abs:,.0f}€)\n\n"
            f"🔗 [Ver anúncio]({listing.source_url})"
        ).replace(",", ".")

    @classmethod
    def format_ai_deal(cls, deal: Dict) -> str:
        """Format an AI-analyzed deal with detailed information."""
        lines = [
            "🤖 *Análise IA — Melhor Oportunidade*",
            "",
        ]

        # Title and score
        title = deal.get('title', 'Imóvel')
        score = deal.get('score', 0)
        discount = deal.get('discount', 0)

        lines.append(f"🏠 *{title}*")
        lines.append(f"⭐ Score: {score:.1f}/10")
        if discount:
            lines.append(f"💰 Desconto: {discount*100:.1f}% abaixo do mercado")
        lines.append("")

        # AI thesis
        thesis = deal.get('thesis', '')
        if thesis:
            lines.append("📝 *Tese de Investimento (IA):*")
            lines.append(thesis)
            lines.append("")

        # Link
        url = deal.get('url', '')
        if url:
            lines.append(f"🔗 [Ver anúncio]({url})")

        message = "\n".join(lines)
        return message[:4096]  # Telegram message limit

    @classmethod
    def format_single_best_opportunity(cls, opportunity: Dict) -> str:
        """Format the single best opportunity with full details and justification.

        Includes:
        - Header, title, price, basic details, location, condition
        - Amenities (garage, pool, elevator, AC, terrace, garden)
        - Kitchen equipment (separate, washer, dishwasher, fridge, stove, oven)
        - Security (shutters, monitoring, video intercom)
        - Valuation (discount, fair value, savings, confidence)
        - Justification of choice (generated text)
        - Score breakdown visual
        - Link
        """
        listing = opportunity["listing"]
        score = opportunity["score"]

        emoji = cls.EMOJI_MAP.get(score.classificacao, "📍")

        # ── Header ──────────────────────────────────────────────────────
        lines = [
            f"{emoji} *{score.classificacao}* — Score {score.score_total:.1f}/10",
            "",
        ]

        # ── Property info ───────────────────────────────────────────────
        titulo = listing.titulo or "Imóvel"
        lines.append(f"🏠 *{titulo}*")

        # Price line
        price = f"{listing.preco_pedido:,.0f}€".replace(",", ".")
        price_m2 = ""
        if listing.preco_por_m2:
            price_m2 = f" ({listing.preco_por_m2:,.0f}€/m²)".replace(",", ".")
        lines.append(f"💵 {price}{price_m2}")

        # Property details
        area = f"{listing.area_util_m2:.0f}m²" if listing.area_util_m2 else "N/D"
        quartos = listing.quartos or 0
        wc = listing.casas_banho or 0
        tipologia = listing.tipologia or ""
        details = f"📐 {area} | 🛏️ {quartos}q | 🚿 {wc}wc"
        if tipologia:
            details += f" | {tipologia}"
        lines.append(details)

        # Location
        freg = listing.freguesia or ""
        conc = listing.concelho or ""
        location = f"{freg}, {conc}".strip(", ")
        if location:
            lines.append(f"📍 {location}")

        # Condition
        estado = listing.estado
        cert = listing.cert_energetico
        ano = listing.ano_construcao
        condition_parts = []
        if estado:
            condition_parts.append(estado.title())
        if ano:
            condition_parts.append(f"Ano: {ano}")
        if cert:
            condition_parts.append(f"Cert: {cert}")
        if condition_parts:
            lines.append(f"🔧 {' | '.join(condition_parts)}")

        lines.append("")

        # ── Amenities ──────────────────────────────────────────────────
        lines.append("🚗 **Amenidades:**")
        lines.append(f"{'✅' if listing.tem_garagem else '❌'} Garagem")
        lines.append(f"{'✅' if listing.tem_piscina else '❌'} Piscina")
        if listing.tem_elevador and listing.andar:
            lines.append(f"✅ Elevador ({listing.andar}º andar)")
        elif listing.tem_elevador:
            lines.append("✅ Elevador")
        else:
            lines.append("❌ Elevador")
        lines.append(f"{'✅' if listing.tem_ac else '❌'} Ar condicionado")
        lines.append(f"{'✅' if listing.tem_terraco else '❌'} Terraço")
        lines.append(f"{'✅' if listing.tem_jardim else '❌'} Jardim")

        lines.append("")

        # ── Kitchen Equipment ───────────────────────────────────────────
        lines.append("🍳 **Equipamento Cozinha:**")
        lines.append(f"{'✅' if listing.cozinha_separada else '❌'} Cozinha separada")
        lines.append(f"{'✅' if listing.tem_maquina_lavar else '❌'} Máquina lavar")
        lines.append(f"{'✅' if listing.tem_maquina_louca else '❌'} Máquina louça")
        lines.append(f"{'✅' if listing.tem_frigorifico else '❌'} Frigorífico")
        lines.append(f"{'✅' if listing.tem_fogao else '❌'} Fogão")
        lines.append(f"{'✅' if listing.tem_forno else '❌'} Forno")

        lines.append("")

        # ── Security ────────────────────────────────────────────────────
        lines.append("🔒 **Segurança:**")
        lines.append(f"{'✅' if listing.tem_estores_anti_roubo else '❌'} Estores anti-roubo")
        lines.append(f"{'✅' if listing.tem_monitorizacao else '❌'} Monitorização")
        lines.append(f"{'✅' if listing.tem_videoporteiro else '❌'} Videoporteiro")

        lines.append("")

        # ── Valuation info ──────────────────────────────────────────────
        if listing.valuations:
            val = listing.valuations[0]
            if val.discount is not None:
                pct = val.discount * 100
                if pct > 0:
                    saving = val.valor_justo - listing.preco_pedido
                    saving_str = f"{saving:,.0f}€".replace(",", ".")
                    valor_str = f"{val.valor_justo:,.0f}€".replace(",", ".")
                    lines.append(f"💰 *{pct:.0f}% abaixo do mercado*")
                    lines.append(f"� Valor estimado: {valor_str} (poupança: {saving_str})")
                elif pct < -5:
                    lines.append(f"⚠️ {abs(pct):.0f}% acima do valor de mercado")
                else:
                    lines.append(f"📊 Preço alinhado com o mercado")

            # Confidence
            if val.confianca is not None:
                conf_pct = val.confianca * 100
                if conf_pct >= 75:
                    lines.append(f"🟢 Confiança: {conf_pct:.0f}%")
                elif conf_pct >= 50:
                    lines.append(f"🟡 Confiança: {conf_pct:.0f}%")
                else:
                    lines.append(f"🔴 Confiança: {conf_pct:.0f}%")

            lines.append("")

        # ── Justification ────────────────────────────────────────────────
        justification = cls._generate_justification(listing, score)
        lines.append("📝 **Por que esta oportunidade:**")
        lines.append(justification)
        lines.append("")

        # ── Score breakdown ─────────────────────────────────────────────
        lines.append("📋 *Análise:*")
        discount_str = f"{score.score_discount:.1f}" if score.score_discount is not None else "N/A"
        location_str = f"{score.score_location:.1f}" if score.score_location is not None else "N/A"
        condition_str = f"{score.score_condition:.1f}" if score.score_condition is not None else "N/A"
        amenities_str = f"{score.score_amenities:.1f}" if score.score_amenities is not None else "N/A"
        liquidity_str = f"{score.score_liquidity:.1f}" if score.score_liquidity is not None else "N/A"
        freshness_str = f"{score.score_freshness:.1f}" if score.score_freshness is not None else "N/A"

        lines.append(f"  Desconto: {cls._bar(score.score_discount)} {discount_str}")
        lines.append(f"  Localização: {cls._bar(score.score_location)} {location_str}")
        lines.append(f"  Condição: {cls._bar(score.score_condition)} {condition_str}")
        lines.append(f"  Amenidades: {cls._bar(score.score_amenities)} {amenities_str}")
        lines.append(f"  Liquidez: {cls._bar(score.score_liquidity)} {liquidity_str}")
        lines.append(f"  Frescura: {cls._bar(score.score_freshness)} {freshness_str}")

        # ── Red flags ───────────────────────────────────────────────────
        if score.red_flags:
            lines.append("")
            for flag in score.red_flags[:3]:
                lines.append(flag)

        # ── Link ────────────────────────────────────────────────────────
        lines.append("")
        lines.append(f"🔗 [Ver anúncio]({listing.source_url})")

        message = "\n".join(lines)
        return message[:4096]  # Telegram message limit

    @classmethod
    def _generate_justification(cls, listing, score) -> str:
        """Generate justification text for why this opportunity was selected.

        Based on:
        - Discount percentage
        - Amenities (garage, elevator, AC, pool)
        - Location score
        - Profit potential
        """
        partes = []

        # Discount
        if listing.valuations and listing.valuations[0].discount:
            discount_pct = listing.valuations[0].discount * 100
            if discount_pct >= 15:
                partes.append(f"Desconto excepcional de {discount_pct:.0f}% abaixo do mercado")
            elif discount_pct >= 10:
                partes.append(f"Desconto atrativo de {discount_pct:.0f}%")
            elif discount_pct >= 5:
                partes.append(f"Desconto razoável de {discount_pct:.0f}%")

        # Amenities
        if listing.tem_garagem:
            partes.append("Com garagem (fator de valor)")
        if listing.tem_elevador and listing.andar and listing.andar > 2:
            partes.append("Elevador (praticidade em andar alto)")
        if listing.tem_ac:
            partes.append("Ar condicionado (conforto térmico)")
        if listing.tem_piscina:
            partes.append("Piscina (valor premium)")

        # Location
        if score.score_location >= 8.0:
            partes.append("Localização excelente")
        elif score.score_location >= 7.0:
            partes.append("Localização muito boa")

        # Profit potential
        if listing.valuations and listing.valuations[0].discount:
            profit = listing.valuations[0].valor_justo - listing.preco_pedido
            if profit > 50000:
                partes.append(f"Lucro potencial de {profit/1000:.0f}k€")
            elif profit > 30000:
                partes.append(f"Lucro potencial de {profit/1000:.0f}k€")

        # Condition
        if score.score_condition >= 8.0:
            partes.append("Condição excelente")
        elif score.score_condition >= 6.0:
            partes.append("Condição boa")

        # If no parts generated, provide default
        if not partes:
            partes.append("Melhor oportunidade disponível")

        return ". ".join(partes) + "."
