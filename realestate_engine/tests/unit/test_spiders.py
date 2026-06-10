"""Unit tests for Scraper Spiders."""
import pytest
from unittest.mock import Mock, patch

from realestate_engine.scraping.spiders.idealista_spider_nodriver import IdealistaSpider
from realestate_engine.scraping.spiders.imovirtual_spider_nodriver import ImovirtualSpider
from realestate_engine.scraping.spiders.casa_sapo_spider_nodriver import CasaSapoSpider
from realestate_engine.scraping.spiders.era_spider_nodriver import ERASpider


class TestScrapers:
    """Basic tests for scraper initialization and configuration."""
    
    def test_idealista_init(self):
        spider = IdealistaSpider()
        assert spider.name == "idealista"
        assert "idealista.pt" in spider.base_url
        assert len(spider.card_selectors) > 0
        assert len(spider.price_selectors) > 0

    def test_imovirtual_init(self):
        spider = ImovirtualSpider()
        assert spider.name == "imovirtual"
        assert "imovirtual.com" in spider.base_url
        assert len(spider.card_selectors) > 0

    def test_casa_sapo_init(self):
        spider = CasaSapoSpider()
        assert spider.name == "casasapo"
        assert "casasapo.pt" in spider.base_url
        
    def test_era_init(self):
        spider = ERASpider()
        assert spider.name == "era"
        assert "era.pt" in spider.base_url
        assert len(spider.card_selectors) > 0

    def test_era_extract_area(self):
        spider = ERASpider()
        assert spider.extract_area_from_text("Apartamento T3 com 120m2") == "120m2"
        assert spider.extract_area_from_text("Casa de 85 m²") == "85 m²"

    def test_era_extract_rooms(self):
        spider = ERASpider()
        assert spider.extract_rooms_from_text("Lindo T3 no centro") == "T3"
        assert spider.extract_rooms_from_text("Apartamento com 2 quartos") == "2 quartos"

