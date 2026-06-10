"""
=== Porto Real Estate Intelligence Engine — Manual Pipeline ===

Este script executa o pipeline completo passo-a-passo:
  1. SCRAPING  → Raspa dados de portais que funcionam sem proxy residencial
  2. ETL       → Normaliza, deduplica, geocodifica e enriquece dados
  3. VALUATION → Treina XGBoost + Haversine Hyper-Local para estimar preço justo
  4. SCORING   → Pontua e classifica oportunidades (0-10)
  5. RESULTADO → Mostra as melhores oportunidades encontradas

Uso:
  py run_scraper_manual.py              (corre tudo, headless)
  py run_scraper_manual.py --visible    (abre browser visível para debug)
  py run_scraper_manual.py --pages 10   (raspa 10 páginas por portal)
"""
import asyncio
import sys
import os
import argparse
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from loguru import logger

# ── Logging ──────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logger.add("logs/engine.log", rotation="10 MB", retention="10 days", level="DEBUG",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
logger.add("logs/errors.log", rotation="5 MB", retention="30 days", level="ERROR",
           backtrace=True, diagnose=True)

from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import Base, get_engine


async def run_pipeline(max_pages: int = 2, headless: bool = True):
    """Run the full end-to-end pipeline."""
    start_time = datetime.now()
    
    # ── Init DB ──────────────────────────────────────────────────────────
    logger.info("=== INICIALIZAR BASE DE DADOS ===")
    repo = DatabaseRepository()
    repo.init_tables()
    
    # ── PASSO 1: SCRAPING ────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("=== PASSO 1: RASPAR CASAS (SCRAPING) ===")
    logger.info("=" * 60)
    
    spider_mgr = SpiderManager()

    # Evidence-based activation (verified end-to-end 2026-04-24):
    #   imovirtual → Next.js __NEXT_DATA__ (direct fetch)
    #   casa_sapo  → embedded schema.org/Offer JSON-LD (direct fetch)
    #   remax      → sitemap + per-listing schema.org/Product JSON-LD (direct fetch)
    working_portals: list[tuple[str, int]] = [
        ("imovirtual", max_pages),
        ("casa_sapo",  max_pages),
        ("remax",      max_pages),
    ]

    # Parked — require browser automation or residential proxies.
    parked_portals = [
        ("era",       "ASP.NET WebForms postback; requires browser or VIEWSTATE reverse-engineering"),
        ("supercasa", "direct IP returns 403; free proxies insufficient"),
        ("century21", "returns 403 + TLS errors on free proxies"),
        ("idealista", "DataDome-protected; free proxies 0 % success"),
        ("olx",       "DataDome-protected; free proxies 0 % success"),
    ]

    from realestate_engine.utils.config import config

    if config.residential_proxy_url:
        logger.info("Proxy Residencial configurado — podemos ativar portais bloqueados em futuras fases.")

    total_raw = 0
    for portal, portal_pages in working_portals:
        try:
            logger.info(f"A raspar {portal} (max {portal_pages} páginas, headless={headless})...")
            results = await spider_mgr.run_spider(portal, max_pages=portal_pages, headless=headless)
            count = len(results)
            total_raw += count
            logger.info(f"  ✓ {portal}: {count} imóveis encontrados")
        except Exception as e:
            logger.exception(f"  ✗ {portal} falhou: {e}")

    for portal, reason in parked_portals:
        logger.info(f"  ⏸ {portal}: inativo — {reason}")
    
    logger.info(f"Total de imóveis brutos encontrados: {total_raw}")
    
    # ── PASSO 2: ETL ─────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("=== PASSO 2: FILTRAR E DEDUPLICAR (ETL) ===")
    logger.info("=" * 60)
    
    try:
        etl = PipelineETL()
        processed = await etl.run(batch_size=10000)
        logger.info(f"  ✓ Casas limpas adicionadas à BD: {processed}")
    except Exception as e:
        logger.exception(f"  ✗ ETL falhou: {e}")
        processed = 0
    
    # ── PASSO 3: VALUATION ───────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("=== PASSO 3: ESTIMATIVA DE PREÇO DE MERCADO (VALUATION) ===")
    logger.info("=" * 60)
    
    try:
        valuation_engine = ValuationEngine()
        valuated = await valuation_engine.valuate_batch(batch_size=10000)
        logger.info(f"  ✓ Casas avaliadas: {valuated}")
    except Exception as e:
        logger.exception(f"  ✗ Valuation falhou: {e}")
        valuated = 0
    
    # ── PASSO 4: SCORING ─────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("=== PASSO 4: PONTUAÇÃO RIGOROSA (SCORING) ===")
    logger.info("=" * 60)
    
    try:
        scoring_engine = ScoringEngine()
        scored = await scoring_engine.score_batch(batch_size=10000)
        logger.info(f"  ✓ Casas pontuadas: {scored}")
    except Exception as e:
        logger.exception(f"  ✗ Scoring falhou: {e}")
        scored = 0
    
    # ── RESULTADO FINAL ──────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("=== RESULTADO FINAL — TOP OPORTUNIDADES ===")
    logger.info("=" * 60)
    
    top_scores = repo.get_top_scores(min_score=5.0, limit=10)
    
    if not top_scores:
        logger.info("Nenhuma casa pontuada acima de 5.0 neste lote.")
        total_listings = repo.get_total_clean_listings_count()
        logger.info(f"Total de listings na BD: {total_listings}")
    else:
        for i, s in enumerate(top_scores, 1):
            l = s.listing
            if not l:
                continue
            v = l.valuations[0] if l.valuations else None
            if v and v.discount:
                discount_str = f"{v.discount*100:+.1f}%"
                profit = l.preco_pedido * abs(v.discount) if v.discount < 0 else 0
                profit_str = f"€{profit:,.0f}"
            else:
                discount_str = "N/A"
                profit_str = "N/A"
            
            fair_val = f"€{v.valor_justo:,.0f}" if v else "?"
            confidence = f"{v.confianca*100:.0f}%" if v and v.confianca else "?"
            
            print(f"\n  #{i} [{s.classificacao}] Score: {s.score_total}/10")
            print(f"     📍 {l.freguesia or '?'}, {l.concelho or '?'}")
            print(f"     🏠 {l.tipologia or '?'} | {l.area_util_m2 or '?'}m² | {l.quartos or '?'} quartos")
            print(f"     💰 Pedem: €{l.preco_pedido:,.0f} | Justo: {fair_val} | Desconto: {discount_str}")
            print(f"     📊 Lucro Potencial: {profit_str} | Confiança: {confidence}")
            # Score breakdown
            if s.score_discount is not None or s.score_location is not None or s.score_condition is not None:
                print(f"     📈 Score breakdown: Desconto={s.score_discount or 0:.1f}, Localização={s.score_location or 0:.1f}, Condição={s.score_condition or 0:.1f}, Amenities={s.score_amenities or 0:.1f}, Liquidez={s.score_liquidity or 0:.1f}, Freshness={s.score_freshness or 0:.1f}")
            if v:
                print(f"     💹 Valuation: Hedonic=€{v.hedonic_value:,.0f}, Comps=€{v.comps_value:,.0f}, INE=€{v.ine_value:,.0f}, XGBoost=€{v.xgboost_value:,.0f}")
            if s.red_flags:
                print(f"     🚩 Red Flags: {', '.join(s.red_flags[:3])}")
    
    # ── RESUMO ───────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"  Pipeline concluído em {elapsed:.1f}s")
    print(f"  Raspados: {total_raw} | Limpos: {processed} | Avaliados: {valuated} | Pontuados: {scored}")
    print(f"  Logs em: logs/engine.log e logs/errors.log")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Porto Real Estate Pipeline")
    parser.add_argument("--pages", type=int, default=2, help="Páginas por portal (default: 2)")
    parser.add_argument("--visible", action="store_true", help="Abre browser visível")
    args = parser.parse_args()
    
    asyncio.run(run_pipeline(max_pages=args.pages, headless=not args.visible))
