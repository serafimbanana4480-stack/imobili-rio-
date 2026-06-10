"""ETL Pipeline for Real Estate Opportunity Engine."""
import asyncio
import inspect
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, RawListing
from realestate_engine.etl.normalizer import Normalizer
from realestate_engine.etl.deduplicator import Deduplicator
from realestate_engine.etl.geocoder import Geocoder
from realestate_engine.etl.enricher import Enricher
from realestate_engine.etl.validator import Validator
from realestate_engine.monitoring.metrics import MetricsCollector
from realestate_engine.monitoring.data_quality import DataQualityEngine
from realestate_engine.utils.decorators import async_timed

metrics = MetricsCollector()
data_quality = DataQualityEngine()


def _sanitize_value(value: Any, expected_type: type = None, field_name: str = "") -> Any:
    """Sanitize a value to ensure it's not a coroutine or other invalid type for DB insertion.

    Defensive measure against 'float() argument must be a string or a real number, not coroutine'.
    """
    if inspect.iscoroutine(value):
        logger.error(f"Coroutine object detected in field '{field_name}' — enrichment method missing await!")
        return None
    if value is None:
        return None
    if expected_type == float:
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning(f"Cannot convert {field_name}={value!r} to float, using None")
            return None
    if expected_type == int:
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(f"Cannot convert {field_name}={value!r} to int, using None")
            return None
    if expected_type == str:
        return str(value)
    return value


class PipelineETL:
    """ETL pipeline: Extract -> Normalize -> Deduplicate -> Geocode -> Enrich -> Validate -> Load."""
    
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.geocoder = Geocoder()
        self.enricher = Enricher()
        self.validator = Validator()
    
    @async_timed
    async def run(self, batch_size: int = 500, validate_urls: bool = False, force_full: bool = False) -> int:
        """Run the full ETL pipeline on a batch of raw listings.
        
        Args:
            batch_size: Maximum number of raw listings to process
            validate_urls: Whether to validate URLs (expensive)
            force_full: If True, process all unprocessed raw listings instead of just new ones
        """

        # Purity guard: fail fast if any fake/sample records exist
        self.repo.assert_no_sample_data()

        if force_full:
            # Process all unprocessed raw listings (backlog mode)
            raw_listings = self.repo.get_unprocessed_raw_listings(limit=batch_size)
            logger.info(f"Force full sync: processing {len(raw_listings)} unprocessed raw listings")
        else:
            # Normal mode: only process new raw listings since last ETL
            last_etl = self.repo.get_last_successful_job_execution("etl.pipeline")
            since = last_etl.finished_at if last_etl and last_etl.finished_at else None
            raw_listings = self.repo.get_raw_listings_since(since, limit=batch_size)
        if not raw_listings:
            logger.info("No new raw listings to process")
            return 0
        
        metrics.record_listings_processed("extract", len(raw_listings))
        
        # Normalize
        normalized = []
        for r in raw_listings:
            n = self.normalizer.normalize(r.raw_data, r.source_portal)
            # Casa Sapo / REMAX store source_id/source_url at record level
            if (not n.get("source_id") or n.get("source_id") == "") and r.source_id:
                n["source_id"] = r.source_id
                logger.debug(f"Restored source_id for {r.source_portal}: {r.source_id}")
            if (not n.get("source_url") or n.get("source_url") == "") and r.source_url:
                n["source_url"] = r.source_url
            normalized.append(n)
        normalized = [n for n in normalized if n["preco_pedido"] and n["area_util_m2"] and n["quartos"] is not None]
        metrics.record_listings_processed("normalize", len(normalized))
        
        # Deduplicate
        existing_fingerprints = self.repo.get_all_fingerprints() if hasattr(self.repo, 'get_all_fingerprints') else set()
        deduplicated = self.deduplicator.filter_duplicates(normalized, existing_fingerprints)
        metrics.record_listings_processed("deduplicate", len(deduplicated))
        
        # Geocode
        for listing in deduplicated:
            if listing.get("morada_raw") and not listing.get("lat"):
                coords = self.geocoder.geocode(listing["morada_raw"])
                if coords:
                    listing["lat"], listing["lon"] = coords
                freg, conc = self.geocoder.extract_freguesia_concelho(listing["morada_raw"])
                if freg and not listing.get("freguesia"):
                    listing["freguesia"] = freg
                if conc and not listing.get("concelho"):
                    listing["concelho"] = conc
        metrics.record_listings_processed("geocode", len(deduplicated))
        
        # Enrich (async)
        enriched = [await self.enricher.enrich(l) for l in deduplicated]
        metrics.record_listings_processed("enrich", len(enriched))
        
        # Validate
        valid, invalid = await self.validator.validate_batch(enriched, validate_url_flag=validate_urls)
        metrics.record_listings_processed("validate", len(valid))
        
        # Load
        clean_listings = []
        for data in valid:
            # Check if listing already exists to update price history
            existing = self.repo.get_clean_listing_by_source(data["source_portal"], data["source_id"])
            
            if existing:
                if existing.preco_pedido != data["preco_pedido"]:
                    logger.info(f"Price change detected for {data['source_portal']}-{data['source_id']}: {existing.preco_pedido} -> {data['preco_pedido']}")
                    from realestate_engine.database.models import PriceHistory
                    history = PriceHistory(
                        listing_id=existing.id,
                        preco=data["preco_pedido"],
                        data=datetime.now(UTC).isoformat(),
                        source="spider"
                    )
                    self.repo.add_price_history(history)
                    
                # Update existing
                self.repo.update_clean_listing(existing.id, data)
                continue

            clean = CleanListing(
                source_portal=_sanitize_value(data.get("source_portal", "unknown"), str, "source_portal"),
                source_id=_sanitize_value(data.get("source_id", ""), str, "source_id"),
                source_url=_sanitize_value(data.get("source_url", ""), str, "source_url"),
                scrape_timestamp=_sanitize_value(data.get("scrape_timestamp", ""), str, "scrape_timestamp"),
                titulo=_sanitize_value(data.get("titulo", ""), str, "titulo"),
                descricao=_sanitize_value(data.get("descricao", ""), str, "descricao"),
                preco_pedido=_sanitize_value(data.get("preco_pedido", 0), float, "preco_pedido"),
                area_util_m2=_sanitize_value(data.get("area_util_m2", 0), float, "area_util_m2"),
                quartos=_sanitize_value(data.get("quartos", 0), int, "quartos"),
                casas_banho=_sanitize_value(data.get("casas_banho"), int, "casas_banho"),
                morada_raw=_sanitize_value(data.get("morada_raw", ""), str, "morada_raw"),
                freguesia=_sanitize_value(data.get("freguesia", ""), str, "freguesia"),
                concelho=_sanitize_value(data.get("concelho", ""), str, "concelho"),
                distrito=_sanitize_value(data.get("distrito", ""), str, "distrito"),
                lat=_sanitize_value(data.get("lat"), float, "lat"),
                lon=_sanitize_value(data.get("lon"), float, "lon"),
                estado=_sanitize_value(data.get("estado", ""), str, "estado"),
                ano_construcao=_sanitize_value(data.get("ano_construcao"), int, "ano_construcao"),
                cert_energetico=_sanitize_value(data.get("cert_energetico", ""), str, "cert_energetico"),
                tipologia=_sanitize_value(data.get("tipologia", ""), str, "tipologia"),
                fotos_urls=_sanitize_value(data.get("fotos_urls", []), list, "fotos_urls"),
                num_fotos=_sanitize_value(data.get("num_fotos", 0), int, "num_fotos"),
                agencia=_sanitize_value(data.get("agencia", ""), str, "agencia"),
                tem_garagem=_sanitize_value(1 if data.get("tem_garagem") else 0, int, "tem_garagem"),
                tem_piscina=_sanitize_value(1 if data.get("tem_piscina") else 0, int, "tem_piscina"),
                tem_vista_mar=_sanitize_value(1 if data.get("tem_vista_mar") else 0, int, "tem_vista_mar"),
                tem_vista_rio=_sanitize_value(1 if data.get("tem_vista_rio") else 0, int, "tem_vista_rio"),
                tem_elevador=_sanitize_value(1 if data.get("tem_elevador") else 0, int, "tem_elevador"),
                tem_terraco=_sanitize_value(1 if data.get("tem_terraco") else 0, int, "tem_terraco"),
                tem_jardim=_sanitize_value(1 if data.get("tem_jardim") else 0, int, "tem_jardim"),
                tem_ac=_sanitize_value(1 if data.get("tem_ac") else 0, int, "tem_ac"),
                andar=_sanitize_value(data.get("andar"), int, "andar"),
                cozinha_separada=_sanitize_value(1 if data.get("cozinha_separada") else 0, int, "cozinha_separada"),
                tem_maquina_lavar=_sanitize_value(1 if data.get("tem_maquina_lavar") else 0, int, "tem_maquina_lavar"),
                tem_maquina_louca=_sanitize_value(1 if data.get("tem_maquina_louca") else 0, int, "tem_maquina_louca"),
                tem_frigorifico=_sanitize_value(1 if data.get("tem_frigorifico") else 0, int, "tem_frigorifico"),
                tem_fogao=_sanitize_value(1 if data.get("tem_fogao") else 0, int, "tem_fogao"),
                tem_forno=_sanitize_value(1 if data.get("tem_forno") else 0, int, "tem_forno"),
                tem_estores_anti_roubo=_sanitize_value(1 if data.get("tem_estores_anti_roubo") else 0, int, "tem_estores_anti_roubo"),
                tem_monitorizacao=_sanitize_value(1 if data.get("tem_monitorizacao") else 0, int, "tem_monitorizacao"),
                tem_videoporteiro=_sanitize_value(1 if data.get("tem_videoporteiro") else 0, int, "tem_videoporteiro"),
                tem_internet=_sanitize_value(1 if data.get("tem_internet") else 0, int, "tem_internet"),
                tem_tv_cabo=_sanitize_value(1 if data.get("tem_tv_cabo") else 0, int, "tem_tv_cabo"),
                tem_telefone=_sanitize_value(1 if data.get("tem_telefone") else 0, int, "tem_telefone"),
                acessibilidade_mobilidade=_sanitize_value(1 if data.get("acessibilidade_mobilidade") else 0, int, "acessibilidade_mobilidade"),
                tem_aquecimento=_sanitize_value(1 if data.get("tem_aquecimento") else 0, int, "tem_aquecimento"),
                despesas_condominio=_sanitize_value(data.get("despesas_condominio"), float, "despesas_condominio"),
                tipo_anunciante=_sanitize_value(data.get("tipo_anunciante", ""), str, "tipo_anunciante"),
                preco_por_m2=_sanitize_value(data.get("preco_por_m2"), float, "preco_por_m2"),
                ine_preco_medio_m2=_sanitize_value(data.get("ine_preco_medio_m2"), float, "ine_preco_medio_m2"),
                ine_tendencia_mensal=_sanitize_value(data.get("ine_tendencia_mensal"), float, "ine_tendencia_mensal"),
                dist_metro_m=_sanitize_value(data.get("dist_metro_m"), float, "dist_metro_m"),
                dist_escola_m=_sanitize_value(data.get("dist_escola_m"), float, "dist_escola_m"),
                dist_comercio_m=_sanitize_value(data.get("dist_comercio_m"), float, "dist_comercio_m"),
            )
            clean_listings.append(clean)
        
        if clean_listings:
            self.repo.create_clean_listings_batch(clean_listings)
            logger.info(f"ETL pipeline completed: loaded {len(clean_listings)} clean listings")

            # Data quality & drift detection (FASE 7)
            try:
                dq_report = data_quality.run_full_check([c.__dict__ for c in clean_listings])
                if not dq_report["healthy"]:
                    logger.warning(f"DataQuality report: {dq_report['drift_alerts']} | anomalies={len(dq_report['price_anomalies'])} | freshness={dq_report['freshness_alerts']}")
                metrics.record_event("etl.data_quality", 1 if dq_report["healthy"] else 0)
            except Exception as e:
                logger.error(f"DataQuality check failed: {e}")
        
        return len(clean_listings)
