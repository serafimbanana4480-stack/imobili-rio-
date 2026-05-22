"""Red flags detector for listings.

Comprehensive detection of suspicious, risky, or low-quality listings with:
- 15+ distinct red flag types
- Severity levels (critical, warning, info)
- Score penalties calibrated per flag
- Description NLP analysis for suspicious keywords
- Price anomaly detection
"""
import re
from typing import List, Dict, Optional, Tuple
from loguru import logger


class RedFlag:
    """Structured red flag with severity and penalty."""

    def __init__(self, code: str, description: str, severity: str, penalty: float):
        self.code = code
        self.description = description
        self.severity = severity      # "critical" | "warning" | "info"
        self.penalty = penalty        # Score points to subtract

    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "description": self.description,
            "severity": self.severity,
            "penalty": self.penalty,
        }

    def __str__(self) -> str:
        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "❓")
        return f"{emoji} {self.description}"


# ── Suspicious description keywords ────────────────────────────────────
CRITICAL_KEYWORDS = [
    "ruina", "ruína", "devoluto", "demolir", "demolição",
    "obras totais", "necessita obras profundas",
    "sem condições de habitabilidade", "insalubre",
    "embargo", "interdição", "ilegal",
]

WARNING_KEYWORDS = [
    "precisa de obras", "necessita renovação", "para recuperar",
    "humidade", "infiltrações", "amianto",
    "placa de fibrocimento", "telhado danificado",
    "sem licença", "não legalizado",
    "herança", "partilhas", "tribunal",
    "vende como está", "venda judicial",
]

POSITIVE_KEYWORDS = [
    "renovado", "remodelado", "novo", "estrear",
    "como novo", "excelente estado", "cozinha equipada",
    "ar condicionado", "aquecimento central",
]


class RedFlagsDetector:
    """Detects red flags in property listings."""

    @classmethod
    def detect(cls, listing: Dict, valuation: Optional[Dict] = None) -> List[str]:
        """Detect red flags and return list of flag descriptions (legacy compat)."""
        flags = cls.detect_detailed(listing, valuation)
        return [str(f) for f in flags]

    @classmethod
    def detect_detailed(cls, listing: Dict, valuation: Optional[Dict] = None) -> List[RedFlag]:
        """Detect red flags with full detail including severity and penalty."""
        flags: List[RedFlag] = []

        preco = listing.get("preco_pedido")
        area = listing.get("area_util_m2")

        # ── 1. CRITICAL: No price ──────────────────────────────────────
        if not preco or preco <= 0:
            flags.append(RedFlag(
                "NO_PRICE", "Preço não especificado — impossível avaliar",
                "critical", 10.0
            ))
            return flags  # Can't evaluate further without price

        # ── 2. CRITICAL: Suspiciously low price/m² ────────────────────
        if area and area > 0:
            p_m2 = preco / area
            if p_m2 < 400:
                flags.append(RedFlag(
                    "PRICE_TOO_LOW",
                    f"Preço/m² de {p_m2:.0f}€ suspeitamente baixo (possível fraude ou erro)",
                    "critical", 5.0
                ))
            elif p_m2 < 700:
                flags.append(RedFlag(
                    "PRICE_VERY_LOW",
                    f"Preço/m² de {p_m2:.0f}€ muito abaixo do mercado — verificar condição",
                    "warning", 1.5
                ))

        # ── 3. CRITICAL: No photos ─────────────────────────────────────
        num_fotos = listing.get("num_fotos", 0) or 0
        if num_fotos == 0:
            flags.append(RedFlag(
                "NO_PHOTOS", "Sem fotos — impossível avaliar estado real",
                "critical", 4.0
            ))
        elif num_fotos < 3:
            flags.append(RedFlag(
                "FEW_PHOTOS", f"Apenas {num_fotos} foto(s) — informação visual insuficiente",
                "warning", 1.0
            ))

        # ── 3b. WARNING: Unusually large area ────────────────────────────
        if area and area > 1000:
            flags.append(RedFlag(
                "VERY_LARGE_AREA",
                f"Área excecionalmente grande ({area:.0f}m²) — verificar se corresponde à realidade",
                "warning", 0.3
            ))

        # ── 4. CRITICAL: No area specified ─────────────────────────────
        if not area or area <= 0:
            flags.append(RedFlag(
                "NO_AREA", "Área útil não especificada — avaliação imprecisa",
                "critical", 3.0
            ))

        # ── 5. WARNING: Severely overpriced ────────────────────────────
        if valuation and valuation.get("discount") is not None:
            discount = valuation["discount"]
            if discount < -0.25:
                flags.append(RedFlag(
                    "SEVERELY_OVERPRICED",
                    f"Sobrevalorizado em {abs(discount)*100:.0f}% acima do valor de mercado",
                    "warning", 2.0
                ))
            elif discount < -0.15:
                flags.append(RedFlag(
                    "OVERPRICED",
                    f"Acima do mercado em {abs(discount)*100:.0f}%",
                    "warning", 1.0
                ))

        # ── 6. WARNING: Low valuation confidence ──────────────────────
        if valuation and valuation.get("confianca") is not None:
            conf = valuation["confianca"]
            if conf < 0.3:
                flags.append(RedFlag(
                    "LOW_CONFIDENCE",
                    "Avaliação com baixa confiança — poucos dados comparáveis",
                    "warning", 0.5
                ))

        # ── 7. WARNING: Very old without renovation ────────────────────
        ano = listing.get("ano_construcao")
        estado = (listing.get("estado") or "").lower()
        renovated_states = {"renovado", "remodelado", "novo", "em_construcao"}
        if ano and ano < 1960 and estado not in renovated_states:
            flags.append(RedFlag(
                "VERY_OLD_NO_RENO",
                f"Construção de {ano} sem renovação — risco de obras pesadas",
                "warning", 1.5
            ))
        elif ano and ano < 1980 and estado not in renovated_states:
            flags.append(RedFlag(
                "OLD_NO_RENO",
                f"Construção de {ano} sem renovação registada",
                "info", 0.3
            ))

        # ── 8. WARNING: Bad energy certificate ─────────────────────────
        cert = (listing.get("cert_energetico") or "").upper().strip()
        if cert in ("F", "G"):
            flags.append(RedFlag(
                "BAD_ENERGY_CERT",
                f"Certificado energético {cert} — custos elevados de energia e possíveis obras de isolamento",
                "warning", 1.0
            ))
        # Removed NO_ENERGY_CERT flag - most listings don't have this data available from portals

        # ── 9. WARNING: Industrial zone ────────────────────────────────
        freg = (listing.get("freguesia") or "").lower()
        morada = (listing.get("morada_raw") or "").lower()
        industrial_words = ["industrial", "zona industrial", "armazém", "lote industrial"]
        if any(w in freg or w in morada for w in industrial_words):
            flags.append(RedFlag(
                "INDUSTRIAL_ZONE",
                "Localização em zona industrial",
                "warning", 1.5
            ))

        # ── 10. WARNING: Area too small for declared rooms ─────────────
        quartos = listing.get("quartos") or 0
        if area and area > 0 and quartos > 0:
            area_per_room = area / (quartos + 1)  # +1 for living area
            if area_per_room < 12:
                flags.append(RedFlag(
                    "TINY_ROOMS",
                    f"Divisões muito pequenas ({area_per_room:.0f}m²/divisão para {quartos} quartos em {area:.0f}m²)",
                    "warning", 1.0
                ))

        # ── 11. WARNING: Very small area (not studio) ──────────────────
        if area and area < 30 and quartos and quartos > 0:
            flags.append(RedFlag(
                "VERY_SMALL",
                f"Área muito reduzida ({area:.0f}m²) para {quartos} quarto(s)",
                "warning", 0.8
            ))

        # ── 12. WARNING: Suspicious description keywords ───────────────
        desc = (listing.get("descricao") or "").lower()
        titulo = (listing.get("titulo") or "").lower()
        full_text = f"{titulo} {desc}"

        for kw in CRITICAL_KEYWORDS:
            if kw in full_text:
                flags.append(RedFlag(
                    "CRITICAL_DESC_KEYWORD",
                    f"Descrição contém '{kw}' — possível problema grave",
                    "critical", 3.0
                ))
                break  # Only one critical keyword flag

        warning_found = []
        for kw in WARNING_KEYWORDS:
            if kw in full_text:
                warning_found.append(kw)
        if warning_found:
            flags.append(RedFlag(
                "SUSPICIOUS_DESC",
                f"Descrição menciona: {', '.join(warning_found[:3])}",
                "warning", 1.0
            ))

        # ── 13. INFO: Long time on market ──────────────────────────────
        dias = listing.get("dias_no_mercado")
        if dias and dias > 180:
            flags.append(RedFlag(
                "LONG_ON_MARKET",
                f"Há {dias} dias no mercado — possível problema oculto ou preço excessivo",
                "info", 0.5
            ))
        elif dias and dias > 90:
            flags.append(RedFlag(
                "MODERATE_MARKET_TIME",
                f"Há {dias} dias no mercado (acima da média)",
                "info", 0.2
            ))

        # ── 14. WARNING: Price inconsistency across portals ────────────
        # (Would need cross-portal data — flagged as TODO)

        # ── 15. INFO: Ground floor without garden ──────────────────────
        andar = listing.get("andar")
        if andar is not None and andar == 0:
            tem_jardim = listing.get("tem_jardim") or False
            if not tem_jardim:
                flags.append(RedFlag(
                    "GROUND_FLOOR",
                    "Rés-do-chão sem jardim — menor privacidade e luminosidade",
                    "info", 0.2
                ))

        return flags

    @classmethod
    def total_penalty(cls, listing: Dict, valuation: Optional[Dict] = None) -> float:
        """Calculate total score penalty from all red flags."""
        flags = cls.detect_detailed(listing, valuation)
        return sum(f.penalty for f in flags)

    @classmethod
    def has_critical_flags(cls, listing: Dict, valuation: Optional[Dict] = None) -> bool:
        """Check if any critical red flags exist."""
        flags = cls.detect_detailed(listing, valuation)
        return any(f.severity == "critical" for f in flags)
