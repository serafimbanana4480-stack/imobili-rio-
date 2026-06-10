"""Unit tests for RedFlagsDetector."""
import pytest
from realestate_engine.scoring.red_flags_detector import RedFlagsDetector, RedFlag


class TestRedFlagsDetector:
    """Test red flag detection logic."""

    def test_no_price_flag(self):
        flags = RedFlagsDetector.detect_detailed({"preco_pedido": None})
        assert any(f.code == "NO_PRICE" for f in flags)

    def test_zero_price_flag(self):
        flags = RedFlagsDetector.detect_detailed({"preco_pedido": 0})
        assert any(f.code == "NO_PRICE" for f in flags)

    def test_no_area_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": None,
        })
        assert any(f.code == "NO_AREA" for f in flags)

    def test_no_photos_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "num_fotos": 0,
        })
        assert any(f.code == "NO_PHOTOS" for f in flags)

    def test_few_photos_warning(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "num_fotos": 2,
        })
        assert any(f.code == "FEW_PHOTOS" for f in flags)

    def test_very_old_no_renovation(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "ano_construcao": 1950,
            "estado": "usado",
        })
        assert any(f.code == "VERY_OLD_NO_RENO" for f in flags)

    def test_old_renovated_no_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "ano_construcao": 1950,
            "estado": "renovado",
        })
        assert not any(f.code == "VERY_OLD_NO_RENO" for f in flags)

    def test_bad_energy_cert(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "cert_energetico": "F",
        })
        assert any(f.code == "BAD_ENERGY_CERT" for f in flags)

    def test_critical_keyword_in_description(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "descricao": "Esta ruína precisa de obras totais",
            "titulo": "Oportunidade",
        })
        assert any(f.code == "CRITICAL_DESC_KEYWORD" for f in flags)

    def test_warning_keyword_in_description(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "descricao": "Imóvel com humidade e precisa de obras",
            "titulo": "T2 Porto",
        })
        assert any(f.code == "SUSPICIOUS_DESC" for f in flags)

    def test_overpriced_severe(self):
        flags = RedFlagsDetector.detect_detailed(
            {"preco_pedido": 300000, "area_util_m2": 80},
            {"discount": -0.30, "confianca": 0.8},
        )
        assert any(f.code == "SEVERELY_OVERPRICED" for f in flags)

    def test_total_penalty(self):
        penalty = RedFlagsDetector.total_penalty(
            {"preco_pedido": 200000, "area_util_m2": None, "num_fotos": 0},
            None,
        )
        assert penalty > 0

    def test_has_critical_flags(self):
        assert RedFlagsDetector.has_critical_flags(
            {"preco_pedido": None}
        )

    def test_no_critical_flags_clean_listing(self):
        assert not RedFlagsDetector.has_critical_flags({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "num_fotos": 10,
            "ano_construcao": 2010,
            "estado": "novo",
            "cert_energetico": "A",
        })

    def test_ground_floor_without_garden(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "andar": 0,
            "tem_jardim": False,
        })
        assert any(f.code == "GROUND_FLOOR" for f in flags)

    def test_ground_floor_with_garden_no_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 80,
            "andar": 0,
            "tem_jardim": True,
        })
        assert not any(f.code == "GROUND_FLOOR" for f in flags)

    def test_tiny_rooms_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 200000,
            "area_util_m2": 40,
            "quartos": 3,
        })
        assert any(f.code == "TINY_ROOMS" for f in flags)

    def test_very_small_area_flag(self):
        flags = RedFlagsDetector.detect_detailed({
            "preco_pedido": 100000,
            "area_util_m2": 25,
            "quartos": 1,
        })
        assert any(f.code == "VERY_SMALL" for f in flags)

    def test_low_confidence_flag(self):
        flags = RedFlagsDetector.detect_detailed(
            {"preco_pedido": 200000, "area_util_m2": 80},
            {"confianca": 0.2},
        )
        assert any(f.code == "LOW_CONFIDENCE" for f in flags)
