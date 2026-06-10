"""Enricher for adding external data to listings.

Enhanced with:
- Full INE market context (median, trend, transaction volume)
- POI distances (metro, school, commerce) with intelligent coordinate caching
- Amenity extraction from description (garage, pool, views)
- Typology inference
- Price per m² calculation
- Computer Vision features (image quality, similarity)
- Advanced NLP features (BERT sentiment, NER, summarization)
"""
import os
import re
from typing import Dict, Optional
from functools import lru_cache
from loguru import logger


def _env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import INEData
from realestate_engine.etl.poi_client import POIClient
from realestate_engine.valuation.ine_client import INEClient
from realestate_engine.etl.geocoder import Geocoder
from sqlalchemy import select

# Heavy/optional dependencies (cv, nlp, features) are loaded lazily so the
# pipeline still boots when torch/transformers/ultralytics are not installed
# (the slim default install). Each loader returns None on ImportError and the
# corresponding enrich_* method becomes a no-op that nulls the output fields.


def _load_heavy_modules():
    """Best-effort lazy import of heavy CV/NLP/feature modules.

    Returns a dict of names mapped to either the imported callable/class or
    None when the dependency is unavailable. Logs a single info line so the
    user understands why heavy features may be skipped.
    """
    mods = {
        "extract_micro_location_features": None,
        "analyze_portuguese_description": None,
        "ImageQualityAnalyzer": None,
        "ImageSimilarityDetector": None,
        "BERTPortugueseProcessor": None,
        "SentimentAnalyzer": None,
        "NERExtractor": None,
        "DescriptionSummarizer": None,
    }
    try:
        from realestate_engine.features.micro_location import extract_micro_location_features
        mods["extract_micro_location_features"] = extract_micro_location_features
    except ImportError as e:
        logger.info(f"micro_location features disabled (missing dep): {e}")
    try:
        from realestate_engine.features.nlp_portuguese import analyze_portuguese_description
        mods["analyze_portuguese_description"] = analyze_portuguese_description
    except ImportError as e:
        logger.info(f"nlp_portuguese features disabled (missing dep): {e}")
    try:
        from realestate_engine.cv.image_quality import ImageQualityAnalyzer
        from realestate_engine.cv.image_similarity import ImageSimilarityDetector
        mods["ImageQualityAnalyzer"] = ImageQualityAnalyzer
        mods["ImageSimilarityDetector"] = ImageSimilarityDetector
    except ImportError as e:
        logger.info(f"CV enrichers disabled (install with: pip install -e .[cv]): {e}")
    try:
        from realestate_engine.nlp.bert_portuguese import BERTPortugueseProcessor
        from realestate_engine.nlp.sentiment_analyzer import SentimentAnalyzer
        from realestate_engine.nlp.ner_extractor import NERExtractor
        from realestate_engine.nlp.summarizer import DescriptionSummarizer
        mods["BERTPortugueseProcessor"] = BERTPortugueseProcessor
        mods["SentimentAnalyzer"] = SentimentAnalyzer
        mods["NERExtractor"] = NERExtractor
        mods["DescriptionSummarizer"] = DescriptionSummarizer
    except ImportError as e:
        logger.info(f"NLP enrichers disabled (install with: pip install -e .[nlp]): {e}")
    return mods


class Enricher:
    """Enriches listings with external data (INE, POIs, amenities)."""

    def __init__(self):
        self.repo = DatabaseRepository()
        self.poi_client = POIClient()
        self.ine_client = INEClient()

        # Lazy-loaded optional heavy modules (None when not installed).
        self._heavy = _load_heavy_modules()
        skip_heavy = _env_flag("ENRICH_SKIP_HEAVY", default=False)

        def _maybe(name):
            cls = self._heavy.get(name)
            if cls is None or skip_heavy:
                return None
            try:
                return cls()
            except Exception as e:  # pragma: no cover - defensive: model load failure
                logger.warning(f"Failed to instantiate {name}: {e}")
                return None

        # CV processors (None when unavailable)
        self.image_quality_analyzer = _maybe("ImageQualityAnalyzer")
        self.image_similarity_detector = _maybe("ImageSimilarityDetector")
        # NLP processors (None when unavailable)
        self.bert_processor = _maybe("BERTPortugueseProcessor")
        self.sentiment_analyzer = _maybe("SentimentAnalyzer")
        self.ner_extractor = _maybe("NERExtractor")
        self.summarizer = _maybe("DescriptionSummarizer")

    def enrich_ine(self, listing: Dict) -> Dict:
        """Add INE price data using the comprehensive INE client."""
        freguesia = listing.get("freguesia", "").strip()
        concelho = listing.get("concelho", "").strip()

        data = self.ine_client.get_data_for_location(freguesia, concelho)

        listing["ine_preco_medio_m2"] = data["median_price"]
        yoy = data.get("yoy_variation", 6.0)
        listing["ine_tendencia_mensal"] = yoy / 12 if yoy else 0.5

        return listing

    @lru_cache(maxsize=512)
    def _poi_cache_key(self, lat_rounded: str, lon_rounded: str, category: str) -> float:
        """Cached POI distance lookup with rounded coordinates (~100m precision).

        Note: This is a helper that delegates to the async POI client.
        The lru_cache here works because we pre-populate via async calls.
        """
        return -1.0  # placeholder; real logic in enrich_pois

    async def enrich_pois(self, listing: Dict) -> Dict:
        """Add Points of Interest distances (async) with coordinate-based caching."""
        lat, lon = listing.get("lat"), listing.get("lon")
        if lat and lon:
            # Round to 3 decimal places (~100m) for cache key to avoid redundant API calls
            lat_r = round(float(lat), 3)
            lon_r = round(float(lon), 3)
            cache_key = (lat_r, lon_r)

            # Check instance-level transient cache (resets per batch) with size limit
            if not hasattr(self, "_poi_transient_cache"):
                self._poi_transient_cache: Dict[tuple, Dict[str, Optional[float]]] = {}

            # Eviction: if cache exceeds 1000 entries, clear oldest 20%
            if len(self._poi_transient_cache) > 1000:
                keys = list(self._poi_transient_cache.keys())
                for k in keys[:len(keys)//5]:
                    del self._poi_transient_cache[k]
                logger.info("POI transient cache evicted 20% oldest entries")

            if cache_key not in self._poi_transient_cache:
                self._poi_transient_cache[cache_key] = {
                    "metro": await self.poi_client.get_nearest_distance(lat_r, lon_r, "metro"),
                    "school": await self.poi_client.get_nearest_distance(lat_r, lon_r, "school"),
                    "market": await self.poi_client.get_nearest_distance(lat_r, lon_r, "market"),
                }
                logger.debug(f"POI cache miss for ({lat_r}, {lon_r})")
            else:
                logger.debug(f"POI cache hit for ({lat_r}, {lon_r})")

            cached = self._poi_transient_cache[cache_key]
            listing["dist_metro_m"] = cached["metro"]
            listing["dist_escola_m"] = cached["school"]
            listing["dist_comercio_m"] = cached["market"]
        return listing

    def enrich_amenities(self, listing: Dict) -> Dict:
        """Extract amenity flags from title and description."""
        title = (listing.get("titulo") or "").lower()
        desc = (listing.get("descricao") or "").lower()
        text = f"{title} {desc}"

        # Garage
        garage_patterns = [
            r"garag[eé]m", r"lugares?\s+de\s+garag", r"box", r"estacionamento",
            r"parking", r"lugar\s+estac", r"garag\.?", r"parqueamento",
            r"estac\.?", r" lugar parking ", r"vaga\s+(?:de\s+)?garag",
        ]
        listing["tem_garagem"] = any(re.search(p, text) for p in garage_patterns)

        # Pool
        pool_patterns = [r"piscina", r"pool"]
        listing["tem_piscina"] = any(re.search(p, text) for p in pool_patterns)

        # Views
        vista_mar_patterns = [r"vista\s+mar", r"sea\s+view", r"frente\s+mar", r"beira[\s-]?mar"]
        listing["tem_vista_mar"] = any(re.search(p, text) for p in vista_mar_patterns)

        vista_rio_patterns = [r"vista\s+rio", r"river\s+view", r"vista\s+douro"]
        listing["tem_vista_rio"] = any(re.search(p, text) for p in vista_rio_patterns)

        # Elevator
        elevator_patterns = [r"elevador", r"elevator", r"lift"]
        listing["tem_elevador"] = any(re.search(p, text) for p in elevator_patterns)

        # Terrace / Balcony
        terrace_patterns = [
            r"terra[cç]os?", r"varandas?", r"balc[ãa]os?", r"terrace", r"balcony",
            r"esplanada", r"loggia", r"loggias", r"terra\s+sol",
        ]
        listing["tem_terraco"] = any(re.search(p, text) for p in terrace_patterns)

        # Garden
        garden_patterns = [r"jardim", r"garden", r"quintal", r"logradouro"]
        listing["tem_jardim"] = any(re.search(p, text) for p in garden_patterns)

        # AC
        ac_patterns = [r"ar\s+condicionado", r"a/?c", r"air\s+condition", r"climatiza"]
        listing["tem_ac"] = any(re.search(p, text) for p in ac_patterns)

        # Floor extraction
        floor_match = re.search(r"(\d+)[º°ª]\s*(?:andar|piso|floor)", text)
        if floor_match:
            listing["andar"] = int(floor_match.group(1))
        elif re.search(r"r[/e]s[\s-]?(?:do[\s-]?ch[aã]o|ch)", text):
            listing["andar"] = 0

        # NEW: Cozinha separada vs open space
        cozinha_separada_patterns = [
            r"cozinha\s+separada", r"cozinha\s+independente", r"cozinha\s+fechada",
            r"cozinha\s+tradicional"
        ]
        listing["cozinha_separada"] = any(re.search(p, text) for p in cozinha_separada_patterns)

        # NEW: Equipamentos
        equipamentos = {
            "tem_maquina_lavar": [r"máquina\s+de\s+lavar", r"washing\s+machine", r"máquina\s+lavar"],
            "tem_maquina_louca": [r"máquina\s+de\s+louça", r"dishwasher", r"máquina\s+louça"],
            "tem_frigorifico": [r"frigorífico", r"frio", r"frigorifico"],
            "tem_fogao": [r"fogão", r"cooker", r"fogao"],
            "tem_forno": [r"forno", r"oven"],
        }
        for campo, patterns in equipamentos.items():
            listing[campo] = any(re.search(p, text) for p in patterns)

        # NEW: Segurança
        seguranca = {
            "tem_estores_anti_roubo": [r"estores?\s+anti\s+roubo", r"anti\s+roubo", r"estores\s+segurança"],
            "tem_monitorizacao": [r"monitoriza[çc]ão", r"surveillance", r"câmaras?", r"cameras?"],
            "tem_videoporteiro": [r"videoporteiro", r"intercomunicador", r"porteiro"],
        }
        for campo, patterns in seguranca.items():
            listing[campo] = any(re.search(p, text) for p in patterns)

        # NEW: Utilidades
        utilidades = {
            "tem_internet": [r"internet", r"wi[- ]?fi", r"fibra"],
            "tem_tv_cabo": [r"tv\s+cabo", r"televisão", r"tv"],
            "tem_telefone": [r"telefone", r"fixo", r"linha\s+telefónica"],
        }
        for campo, patterns in utilidades.items():
            listing[campo] = any(re.search(p, text) for p in patterns)

        # NEW: Acessibilidade
        acessibilidade_patterns = [
            r"acessibilidade", r"mobilidade\s+reduzida", r"rampa", r"acessível",
            r"sem\s+barreiras"
        ]
        listing["acessibilidade_mobilidade"] = any(
            re.search(p, text) for p in acessibilidade_patterns
        )

        # NEW: Aquecimento
        aquecimento_patterns = [
            r"aquecimento", r"central", r"radiador", r"piso\s+radiante", r"climatização"
        ]
        listing["tem_aquecimento"] = any(re.search(p, text) for p in aquecimento_patterns)

        # NEW: Despesas de condomínio
        despesas_match = re.search(r"cond[oô]min[ií]o\s*[:=]?\s*([0-9.,]+)\s*€", text)
        if despesas_match:
            try:
                listing["despesas_condominio"] = float(
                    despesas_match.group(1).replace(".", "").replace(",", ".")
                )
            except ValueError:
                pass

        # NEW: Tipo de anunciante
        if re.search(r"particular", text):
            listing["tipo_anunciante"] = "particular"
        elif re.search(r"profissional|imobiliária|agência", text):
            listing["tipo_anunciante"] = "profissional"

        return listing

    def enrich_price_metrics(self, listing: Dict) -> Dict:
        """Calculate derived price metrics."""
        preco = listing.get("preco_pedido")
        area = listing.get("area_util_m2")

        if preco and area and area > 0:
            listing["preco_por_m2"] = round(preco / area, 2)
        else:
            listing.setdefault("preco_por_m2", None)

        return listing

    def enrich_nlp_features(self, listing: Dict) -> Dict:
        """Enrich listing with Portuguese NLP features."""
        analyze_fn = self._heavy.get("analyze_portuguese_description")
        if analyze_fn is None:
            return listing
        try:
            title = listing.get("titulo", "")
            description = listing.get("descricao", "")

            nlp_features = analyze_fn(title, description)
            listing.update(nlp_features)
            logger.debug(f"Added NLP features to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"NLP enrichment failed for listing {listing.get('source_id', '')}: {e}")
        return listing

    def enrich_micro_location(self, listing: Dict) -> Dict:
        """Enrich listing with micro-location features."""
        extract_fn = self._heavy.get("extract_micro_location_features")
        if extract_fn is None:
            return listing
        try:
            micro_features = extract_fn(listing)
            listing.update(micro_features)
            logger.debug(f"Added micro-location features to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"Micro-location enrichment failed for listing {listing.get('source_id', '')}: {e}")
        return listing

    def enrich_image_quality(self, listing: Dict) -> Dict:
        """Enrich listing with image quality analysis."""
        if self.image_quality_analyzer is None:
            listing.setdefault("image_quality_score", None)
            listing.setdefault("image_blur_score", None)
            listing.setdefault("image_brightness_score", None)
            return listing
        try:
            fotos_urls = listing.get("fotos_urls", [])
            if not isinstance(fotos_urls, list) or not fotos_urls:
                listing["image_quality_score"] = None
                listing["image_blur_score"] = None
                listing["image_brightness_score"] = None
                return listing
            
            # Analyze first image as representative
            first_image_url = fotos_urls[0]
            quality_result = self.image_quality_analyzer.analyze_image(first_image_url)
            
            listing["image_quality_score"] = quality_result.get("image_quality_score")
            listing["image_blur_score"] = quality_result.get("blur_score")
            listing["image_brightness_score"] = quality_result.get("brightness_score")
            
            logger.debug(f"Added image quality to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"Image quality enrichment failed for listing {listing.get('source_id', '')}: {e}")
            listing["image_quality_score"] = None
            listing["image_blur_score"] = None
            listing["image_brightness_score"] = None
        return listing

    def enrich_image_similarity(self, listing: Dict) -> Dict:
        """Enrich listing with image perceptual hash for duplicate detection."""
        if self.image_similarity_detector is None:
            listing.setdefault("image_phash", None)
            return listing
        try:
            fotos_urls = listing.get("fotos_urls", [])
            if not isinstance(fotos_urls, list) or not fotos_urls:
                listing["image_phash"] = None
                return listing
            
            # Calculate pHash for first image
            first_image_url = fotos_urls[0]
            phash = self.image_similarity_detector.calculate_phash(first_image_url)
            listing["image_phash"] = phash
            
            logger.debug(f"Added image pHash to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"Image similarity enrichment failed for listing {listing.get('source_id', '')}: {e}")
            listing["image_phash"] = None
        return listing

    def enrich_bert_sentiment(self, listing: Dict) -> Dict:
        """Enrich listing with BERT-based sentiment analysis."""
        if self.sentiment_analyzer is None:
            listing.setdefault("bert_sentiment_score", None)
            listing.setdefault("bert_sentiment_label", None)
            return listing
        try:
            description = listing.get("descricao", "")
            if not description:
                listing["bert_sentiment_score"] = None
                listing["bert_sentiment_label"] = None
                return listing
            
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(description)
            listing["bert_sentiment_score"] = sentiment_result.get("sentiment_score")
            listing["bert_sentiment_label"] = sentiment_result.get("sentiment_label")
            
            logger.debug(f"Added BERT sentiment to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"BERT sentiment enrichment failed for listing {listing.get('source_id', '')}: {e}")
            listing["bert_sentiment_score"] = None
            listing["bert_sentiment_label"] = None
        return listing

    def enrich_ner_entities(self, listing: Dict) -> Dict:
        """Enrich listing with named entity extraction."""
        if self.ner_extractor is None:
            listing.setdefault("extracted_entities", None)
            return listing
        try:
            description = listing.get("descricao", "")
            if not description:
                listing["extracted_entities"] = None
                return listing
            
            entities = self.ner_extractor.extract_entities(description)
            listing["extracted_entities"] = entities
            
            logger.debug(f"Added NER entities to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"NER enrichment failed for listing {listing.get('source_id', '')}: {e}")
            listing["extracted_entities"] = None
        return listing

    def enrich_description_summary(self, listing: Dict) -> Dict:
        """Enrich listing with description summary."""
        if self.summarizer is None:
            listing.setdefault("description_summary", listing.get("descricao", "")[:200] if listing.get("descricao") else None)
            return listing
        try:
            description = listing.get("descricao", "")
            if not description or len(description) < 200:
                listing["description_summary"] = description
                return listing
            
            summary = self.summarizer.summarize(description, max_length=150)
            listing["description_summary"] = summary
            
            logger.debug(f"Added description summary to listing {listing.get('source_id', '')}")
        except Exception as e:
            logger.warning(f"Description summarization failed for listing {listing.get('source_id', '')}: {e}")
            listing["description_summary"] = listing.get("descricao", "")[:200]
        return listing

    async def enrich(self, listing: Dict) -> Dict:
        """Apply enrichment steps in order (async).

        Heavy enrichers (image download + CV analysis, BERT sentiment, NER,
        summariser) can add ~2-5 s per listing, which makes bootstrap runs on
        hundreds of records take tens of minutes. They can be toggled off by
        setting ``ENRICH_SKIP_HEAVY=1`` in the environment; the pipeline then
        populates only cheap, fully-local features (INE context, amenity
        regex, rule-based NLP, micro-location).
        """
        listing = self.enrich_ine(listing)
        listing = await self.enrich_pois(listing)
        listing = self.enrich_amenities(listing)
        listing = self.enrich_nlp_features(listing)  # Portuguese NLP analysis
        listing = self.enrich_micro_location(listing)
        listing = self.enrich_price_metrics(listing)

        if not _env_flag("ENRICH_SKIP_HEAVY", default=False):
            # CV enrichment (network I/O + CV analysis)
            listing = self.enrich_image_quality(listing)
            listing = self.enrich_image_similarity(listing)
            # Advanced NLP enrichment (BERT inference on CPU)
            listing = self.enrich_bert_sentiment(listing)
            listing = self.enrich_ner_entities(listing)
            listing = self.enrich_description_summary(listing)
        else:
            # Null out fields so downstream code doesn't KeyError
            for key in (
                "image_quality_score", "image_blur_score", "image_brightness_score",
                "image_phash", "bert_sentiment_score", "bert_sentiment_label",
                "extracted_entities", "description_summary",
            ):
                listing.setdefault(key, None)

        logger.debug(
            f"Enriched listing {listing.get('source_id', '')} - "
            f"INE: {listing.get('ine_preco_medio_m2')}e/m², "
            f"Garagem: {listing.get('tem_garagem')}, "
            f"Vista mar: {listing.get('tem_vista_mar')}, "
            f"Location Quality: {listing.get('location_quality_index', 'N/A')}, "
            f"NLP Score: {listing.get('description_quality_score', 'N/A')}, "
            f"Image Quality: {listing.get('image_quality_score', 'N/A')}, "
            f"BERT Sentiment: {listing.get('bert_sentiment_label', 'N/A')}"
        )
        return listing
