"""Unit tests for NationalScrapingSystem region mapping and municipality coverage."""
from realestate_engine.scraping.national_scraping_system import NationalScrapingSystem, RegionalPriorityManager


class TestNationalScrapingSystem:
    """Test national scraping system coverage helpers."""

    def test_all_municipalities_count_is_308(self):
        manager = RegionalPriorityManager()
        municipalities = manager._get_all_municipalities()
        assert len(municipalities) == 308
        assert len(set(municipalities)) == 308

    def test_group_municipalities_by_region_maps_islands_correctly(self):
        system = NationalScrapingSystem()
        municipalities = {
            "Funchal": 1.0,
            "Ponta Delgada": 1.0,
            "Lisboa": 1.0,
            "Porto": 1.0,
        }
        grouped = system._group_municipalities_by_region(municipalities)

        assert "Funchal" in grouped["madeira"]
        assert "Ponta Delgada" in grouped["acores"]
        assert "Lisboa" in grouped["lisboa"]
        assert "Porto" in grouped["norte"]

    def test_group_municipalities_by_region_defaults_unknown_to_norte(self):
        system = NationalScrapingSystem()
        municipalities = {"Municipio Desconhecido": 1.0}
        grouped = system._group_municipalities_by_region(municipalities)
        assert "Municipio Desconhecido" in grouped["norte"]

    def test_group_municipalities_by_region_covers_all_regions(self):
        system = NationalScrapingSystem()
        municipalities = {
            "Porto": 1.0,
            "Coimbra": 1.0,
            "Lisboa": 1.0,
            "Evora": 1.0,  # Normalized to avoid encoding issues
            "Faro": 1.0,
            "Funchal": 1.0,
            "Ponta Delgada": 1.0,
        }

        grouped = system._group_municipalities_by_region(municipalities)

        assert "Porto" in grouped["norte"]
        assert "Coimbra" in grouped["centro"]
        assert "Lisboa" in grouped["lisboa"]
        assert "Evora" in grouped["alentejo"]
        assert "Faro" in grouped["algarve"]
        assert "Funchal" in grouped["madeira"]
        assert "Ponta Delgada" in grouped["acores"]

    def test_group_municipalities_by_region_does_not_drop_known_municipalities(self):
        system = NationalScrapingSystem()
        municipalities = {
            "Lisboa": 1.0,
            "Porto": 1.0,
            "Braga": 1.0,
            "Faro": 1.0,
            "Setubal": 1.0,
        }

        grouped = system._group_municipalities_by_region(municipalities)

        flattened = sum(grouped.values(), [])
        assert set(flattened) == set(municipalities.keys())
