"""Spider registry for centralized spider class management.

Replaces dynamic try/except imports with a clean registry pattern
for better testability and maintainability.
"""
from typing import Dict, Type, Optional, List
from loguru import logger


class SpiderRegistry:
    """Central registry for spider classes with lazy loading."""

    _instance: Optional["SpiderRegistry"] = None
    _spiders: Dict[str, Type] = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, spider_cls: Type):
        cls._spiders[name] = spider_cls
        logger.debug(f"Registered spider: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        if not cls._initialized:
            cls._discover()
        return cls._spiders.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Type]:
        if not cls._initialized:
            cls._discover()
        return dict(cls._spiders)

    @classmethod
    def get_available_names(cls) -> List[str]:
        if not cls._initialized:
            cls._discover()
        return list(cls._spiders.keys())

    @classmethod
    def _discover(cls):
        if cls._initialized:
            return
        cls._initialized = True

        # Tier 1 - Nacionais
        _try_import(cls, "idealista", "realestate_engine.scraping.spiders.idealista_spider_nodriver", "IdealistaSpider")
        _try_import(cls, "imovirtual", "realestate_engine.scraping.spiders.imovirtual_nextdata_spider", "ImovirtualNextDataSpider")
        _try_import(cls, "imovirtual", "realestate_engine.scraping.spiders.imovirtual_spider_nodriver", "ImovirtualSpider")
        _try_import(cls, "casa_sapo", "realestate_engine.scraping.spiders.casa_sapo_direct_spider", "CasaSapoDirectSpider")
        _try_import(cls, "casa_sapo", "realestate_engine.scraping.spiders.casa_sapo_spider_nodriver", "CasaSapoSpider")
        _try_import(cls, "olx", "realestate_engine.scraping.spiders.olx_spider_nodriver", "OLXSpider")

        # Tier 2 - Bancários
        _try_import(cls, "bpi", "realestate_engine.scraping.spiders.bpi_spider_nodriver", "BPISpider")
        _try_import(cls, "caixa", "realestate_engine.scraping.spiders.caixa_spider_nodriver", "CaixaSpider")
        _try_import(cls, "santander", "realestate_engine.scraping.spiders.santander_spider_nodriver", "SantanderSpider")
        _try_import(cls, "millennium", "realestate_engine.scraping.spiders.millennium_spider_nodriver", "MillenniumSpider")

        # Tier 3 - Regionais
        _try_import(cls, "era", "realestate_engine.scraping.spiders.era_spider_nodriver", "ERASpider")
        _try_import(cls, "remax", "realestate_engine.scraping.spiders.remax_direct_spider", "REMAXDirectSpider")
        _try_import(cls, "remax", "realestate_engine.scraping.spiders.remax_spider_nodriver", "REMAXSpider")
        _try_import(cls, "supercasa", "realestate_engine.scraping.spiders.supercasa_spider_nodriver", "SuperCasaSpider")
        _try_import(cls, "century21", "realestate_engine.scraping.spiders.century21_spider_nodriver", "Century21Spider")

        logger.info(f"SpiderRegistry discovered {len(cls._spiders)} spiders")


def _try_import(registry_cls, name: str, module_path: str, class_name: str):
    try:
        import importlib
        module = importlib.import_module(module_path)
        spider_cls = getattr(module, class_name)
        registry_cls.register(name, spider_cls)
    except (ImportError, AttributeError):
        pass
