"""Amenities score calculator (15% weight).

Calculates score based on structural features that impact property value:
- Essential amenities (garage, AC, separated kitchen)
- Important amenities (elevator, equipment, security)
- Premium amenities (pool, garden, terrace)
"""
from typing import Optional
from loguru import logger


class ScoreAmenitiesCalculator:
    """Calculates amenities score based on structural features."""

    @classmethod
    def calculate(
        cls,
        tem_garagem: Optional[int] = None,
        tem_piscina: Optional[int] = None,
        tem_elevador: Optional[int] = None,
        tem_ac: Optional[int] = None,
        tem_terraco: Optional[int] = None,
        tem_jardim: Optional[int] = None,
        cozinha_separada: Optional[int] = None,
        tem_maquina_lavar: Optional[int] = None,
        tem_maquina_louca: Optional[int] = None,
        tem_frigorifico: Optional[int] = None,
        tem_fogao: Optional[int] = None,
        tem_forno: Optional[int] = None,
        tem_estores_anti_roubo: Optional[int] = None,
        tem_monitorizacao: Optional[int] = None,
        tem_videoporteiro: Optional[int] = None,
        andar: Optional[int] = None,
    ) -> float:
        """Calculate amenities score (0-10)."""
        score = 5.0  # Default: unknown amenities

        # ── Essential amenities (high impact) ─────────────────────────────
        if tem_garagem:
            score += 1.0
        if tem_ac:
            score += 0.8
        if cozinha_separada:
            score += 0.5

        # ── Important amenities (medium impact) ─────────────────────────
        if tem_elevador:
            score += 0.5
        if andar is not None and andar > 0:
            # Higher floors are slightly better (light, view)
            if andar <= 3:
                score += 0.1
            elif andar <= 6:
                score += 0.2
            else:
                score += 0.3

        # Count equipment
        equipment_count = sum([
            tem_maquina_lavar or 0,
            tem_maquina_louca or 0,
            tem_frigorifico or 0,
            tem_fogao or 0,
            tem_forno or 0,
        ])
        if equipment_count >= 3:
            score += 0.5
        elif equipment_count >= 2:
            score += 0.3
        elif equipment_count >= 1:
            score += 0.1

        # Count security features
        security_count = sum([
            tem_estores_anti_roubo or 0,
            tem_monitorizacao or 0,
            tem_videoporteiro or 0,
        ])
        if security_count >= 2:
            score += 0.3
        elif security_count >= 1:
            score += 0.1

        # ── Premium amenities (bonus impact) ─────────────────────────────
        if tem_piscina:
            score += 0.8
        if tem_jardim:
            score += 0.5
        if tem_terraco:
            score += 0.3

        # ── Penalty for missing essential amenities ───────────────────────
        # If no garage, AC, or separated kitchen, penalize
        essential_missing = sum([
            not tem_garagem,
            not tem_ac,
            not cozinha_separada,
        ])
        if essential_missing == 3:
            score -= 0.5
        elif essential_missing == 2:
            score -= 0.3
        elif essential_missing == 1:
            score -= 0.1

        return max(0.0, min(10.0, round(score, 2)))
