"""Scraping Results page — live feedback during scraping/ETL/valuation/scoring.

Key UX guarantees:
- Pre-flight checks (DB / browser / Redis / spiders) before any pipeline call.
- Per-portal loop with status updates between portals (no 4h-long opaque wait).
- Tail of the on-disk log file polled between stages so the UI keeps moving.
- Quick Demo button: HTTP-only ``casa_sapo_direct`` spider for ~30s validation.
- Per-portal exceptions surfaced (not silently swallowed).
"""
import streamlit as st
import pandas as pd
import sys
import os
import asyncio
import traceback
from datetime import datetime
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.scraping.spider_manager import SpiderManager
from realestate_engine.etl.pipeline_etl import PipelineETL
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.investor_tools.listing_janitor import ListingJanitor

# Tail this log file in the UI between stages — written to by loguru via
# realestate_engine.dashboard.__init__ + realestate_engine logging setup.
_LOG_FILE_CANDIDATES: List[Path] = [
    Path(project_root) / "logs" / "app" / "dashboard.log",
    Path(project_root) / "logs" / "engine.log",
    Path(project_root) / "logs" / "app" / "errors.log",
]


def _run_async(coro):
    """Run async work from Streamlit without leaking the event loop.
    
    On Windows, configures ProactorEventLoop to enable subprocess support
    required by nodriver's Chrome launcher (asyncio.create_subprocess_exec).
    """
    if sys.platform == "win32":
        # Windows requires ProactorEventLoop for subprocess support
        original_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            return asyncio.run(coro)
        finally:
            asyncio.set_event_loop_policy(original_policy)
    else:
        return asyncio.run(coro)


def _tail_log_file(lines: int = 80) -> str:
    """Return the last ``lines`` lines of the most recent existing log file.

    Falls back to an empty string if no log file is readable. Reads in binary
    + tail-walks bytes from the end to avoid loading huge files into memory.
    """
    for path in _LOG_FILE_CANDIDATES:
        try:
            if not path.exists() or path.stat().st_size == 0:
                continue
            with path.open("rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                # Read at most ~64KB from the end — enough for ~600 lines.
                read_size = min(size, 64 * 1024)
                f.seek(size - read_size, os.SEEK_SET)
                tail_bytes = f.read()
            try:
                text = tail_bytes.decode("utf-8", errors="replace")
            except Exception:
                text = tail_bytes.decode("latin-1", errors="replace")
            return "\n".join(text.splitlines()[-lines:])
        except Exception:
            continue
    return ""


def _preflight_checks(repo: DatabaseRepository) -> Dict[str, Dict[str, str]]:
    """Run quick health checks before launching the pipeline.

    Returns a dict ``{component: {"status": ok|warn|error, "detail": str}}``
    so the caller can decide whether to block (DB error) or merely warn.
    """
    results: Dict[str, Dict[str, str]] = {}

    # 1. Database
    try:
        with repo.Session() as s:
            s.execute  # noqa: B018 — just touch the attribute
        total = repo.get_total_clean_listings_count()
        results["DB"] = {"status": "ok", "detail": f"OK — {total} clean listings"}
    except Exception as e:  # noqa: BLE001
        results["DB"] = {"status": "error", "detail": f"{type(e).__name__}: {e}"}

    # 2. Browser (optional — only blocks nodriver spiders)
    try:
        from realestate_engine.scraping.browser_resolver import find_browser
        path = find_browser()
        if path:
            results["Browser"] = {"status": "ok", "detail": str(path)}
        else:
            results["Browser"] = {
                "status": "warn",
                "detail": "Não encontrado — spiders nodriver desativados (HTTP-only continua a funcionar)",
            }
    except Exception as e:  # noqa: BLE001
        results["Browser"] = {"status": "warn", "detail": f"resolver falhou: {e}"}

    # 3. Redis
    try:
        from realestate_engine.infrastructure.redis_client import get_redis
        cache = get_redis()
        if cache.healthy():
            results["Redis"] = {"status": "ok", "detail": "saudável"}
        else:
            results["Redis"] = {
                "status": "warn",
                "detail": "indisponível — rate limit em modo fail-open",
            }
    except Exception as e:  # noqa: BLE001
        results["Redis"] = {"status": "warn", "detail": f"check falhou: {e}"}

    # 4. Spiders disponíveis
    try:
        mgr = SpiderManager()
        loaded = [p for p in SpiderManager.DEFAULT_CYCLE_PORTALS
                  if mgr._get_spider_class(p) is not None]
        missing = [p for p in SpiderManager.DEFAULT_CYCLE_PORTALS if p not in loaded]
        if not loaded:
            results["Spiders"] = {"status": "error", "detail": "nenhum spider carregou"}
        else:
            detail = f"{len(loaded)}/{len(SpiderManager.DEFAULT_CYCLE_PORTALS)} carregados"
            if missing:
                detail += f" — em falta: {', '.join(missing)}"
            results["Spiders"] = {
                "status": "ok" if not missing else "warn",
                "detail": detail,
            }
    except Exception as e:  # noqa: BLE001
        results["Spiders"] = {"status": "error", "detail": f"{type(e).__name__}: {e}"}

    return results


def _render_preflight(results: Dict[str, Dict[str, str]]) -> bool:
    """Render pre-flight results and return True if the pipeline can proceed."""
    cols = st.columns(len(results))
    blocking = False
    for col, (name, info) in zip(cols, results.items()):
        with col:
            label = f"**{name}**"
            status, detail = info["status"], info["detail"]
            if status == "ok":
                st.success(f"{label}\n\n {detail}")
            elif status == "warn":
                st.warning(f"{label}\n\n {detail}")
            else:
                st.error(f"{label}\n\n {detail}")
                if name == "DB":
                    blocking = True
    return not blocking


class _LogCapture:
    """Capture loguru output to an in-memory buffer for live display."""

    def __init__(self, max_lines: int = 400):
        self.buffer: deque[str] = deque(maxlen=max_lines)
        self._handler_id = None

    def _sink(self, message):
        self.buffer.append(str(message).rstrip())

    def __enter__(self):
        self._handler_id = logger.add(self._sink, level="INFO",
                                       format="{time:HH:mm:ss} | {level: <7} | {message}")
        return self

    def __exit__(self, *exc):
        if self._handler_id is not None:
            try:
                logger.remove(self._handler_id)
            except Exception:
                pass

    def text(self) -> str:
        return "\n".join(self.buffer)


def _refresh_log_panel(placeholder, captured: "_LogCapture") -> None:
    """Render the merged in-memory + on-disk log into the placeholder."""
    in_memory = captured.text()
    on_disk = _tail_log_file(lines=60)
    body = in_memory if in_memory else on_disk
    if in_memory and on_disk:
        body = f"{in_memory}\n--- tail({_LOG_FILE_CANDIDATES[0].name}) ---\n{on_disk}"
    placeholder.code(body or "(sem logs ainda)", language="log")


def _run_pipeline_post_scrape(
    repo: DatabaseRepository,
    status,
    captured: "_LogCapture",
    log_placeholder,
    raw_total: int,
    before_total: int,
) -> Dict[str, int]:
    """Run ETL + valuation + scoring after scraping; return counts dict."""
    counts: Dict[str, int] = {"etl": 0, "valuation": 0, "scoring": 0}

    status.update(label=" ETL: normalização + deduplicação...", state="running")
    counts["etl"] = _run_async(PipelineETL().run(batch_size=100000, force_full=True))
    duplicates = max(0, raw_total - counts["etl"])
    st.write(f"**ETL concluído:** {counts['etl']} novos limpos | {duplicates} duplicados")
    _refresh_log_panel(log_placeholder, captured)

    status.update(label=" Valuation (estimativa de valor)...", state="running")
    counts["valuation"] = _run_async(ValuationEngine().valuate_batch(batch_size=100000))
    st.write(f"**Valuation:** {counts['valuation']} avaliados")
    _refresh_log_panel(log_placeholder, captured)

    status.update(label=" Scoring (classificação de oportunidade)...", state="running")
    counts["scoring"] = _run_async(ScoringEngine().score_batch(batch_size=100000))
    st.write(f"**Scoring:** {counts['scoring']} classificados")
    _refresh_log_panel(log_placeholder, captured)

    after_total = repo.get_total_clean_listings_count()
    counts["new_in_db"] = max(0, after_total - before_total)
    counts["duplicates"] = duplicates
    return counts


def render_scraping_results():
    """Render scraping results page with final results only."""
    st.title(" Resultados de Scraping")
    st.markdown("*Casas raspadas com preço, valor de mercado e score*")

    repo = DatabaseRepository()

    #  Quick Links / Shortcuts 
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(" Ver Overview", width="stretch"):
            st.session_state['page'] = " Início"
            st.rerun()
    
    with col2:
        if st.button(" Pesquisa Avançada", width="stretch"):
            st.session_state['page'] = " Pesquisar"
            st.rerun()
    
    with col3:
        if st.button(" Análise Mercado", width="stretch"):
            st.session_state['page'] = " Análise"
            st.session_state['analysis_page'] = " Mercado"
            st.rerun()

    st.markdown("---")

    #  Pre-flight checks (always shown) 
    st.markdown("###  Pre-flight")
    st.caption("Verificações rápidas antes de executar o pipeline. Bloqueia só se DB falhar.")
    preflight = _preflight_checks(repo)
    can_run = _render_preflight(preflight)

    #  Run Scraping Buttons 
    st.markdown("###  Execução")
    col1, col2, col3 = st.columns(3)

    with col1:
        run_full = st.button(
            " Pipeline Completo",
            type="primary", width="stretch",
            disabled=not can_run,
            help="Scraping de todos os portais + ETL + Valuation + Scoring (~10–60min)",
        )
    with col2:
        run_rapid = st.button(
            " Rápido Inteligente (~5min)",
            width="stretch",
            disabled=not can_run,
            help="Execução inteligente: todos os portais (2 páginas), ETL Skip Heavy, Geocoder Fast. (~5-10min)",
        )
    with col3:
        if st.button(" Atualizar Dados", width="stretch"):
            st.session_state['scraping_running'] = False
            st.rerun()

    if run_full or run_rapid:
        before_total = repo.get_total_clean_listings_count()
        
        # If rapid mode, we use the Orchestrator's rapid logic or simulate it here
        if run_rapid:
            mode_label = "Rápido Inteligente"
            portals = list(SpiderManager.DEFAULT_CYCLE_PORTALS)
            max_pages = 2
            os.environ["ENRICH_SKIP_HEAVY"] = "1"
            os.environ["GEOCAPE_FORCE_FAST"] = "1"
        else:
            mode_label = "Pipeline Completo"
            portals = list(SpiderManager.DEFAULT_CYCLE_PORTALS)
            max_pages = 20
            # Ensure heavy features are enabled for full run
            os.environ.pop("ENRICH_SKIP_HEAVY", None)
            os.environ.pop("GEOCAPE_FORCE_FAST", None)
        
        _run_main_pipeline(repo, mode_label, portals, max_pages, before_total)

    #  Maintenance Buttons 
    st.markdown("###  Limpeza e Manutenção")
    st.caption("Verifique casas repetidas ou anúncios que já não estão disponíveis.")
    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        run_dedup = st.button(
            " Procurar Repetidos",
            width="stretch",
            help="Usa IA/Fuzzy Match para encontrar a mesma casa em diferentes portais.",
        )
    with col_m2:
        run_ghost = st.button(
            " Check Disponibilidade",
            width="stretch",
            help="Verifica se os links ainda funcionam. Remove casas vendidas/removidas.",
        )

    if run_dedup:
        with st.status(" A procurar duplicados...", expanded=True) as status:
            janitor = ListingJanitor(repo)
            count = _run_async(janitor.run_deduplication())
            if count > 0:
                status.update(label=f" Limpeza concluída: {count} duplicados marcados.", state="complete")
                st.success(f"Foram encontrados e marcados {count} anúncios repetidos.")
            else:
                status.update(label=" Tudo limpo! Não foram encontrados duplicados novos.", state="complete")
                st.info("A sua base de dados já está otimizada.")
        st.rerun()

    if run_ghost:
        with st.status(" A verificar disponibilidade dos anúncios...", expanded=True) as status:
            janitor = ListingJanitor(repo)
            # Check a batch of 50 oldest active listings
            results = _run_async(janitor.check_availability(batch_size=50))
            checked = results["checked"]
            removed = results["removed"]
            status.update(label=f" Verificação concluída. ({checked} verificados, {removed} removidos)", state="complete")
            if removed > 0:
                st.warning(f"Removidos {removed} anúncios que já não estavam disponíveis no portal.")
            else:
                st.success(f"Todos os {checked} anúncios verificados continuam ativos.")
        st.rerun()


def _run_main_pipeline(repo, mode_label, portals, max_pages, before_total):
    """Helper to run the full/rapid pipeline logic."""
    log_placeholder = st.empty()
    per_portal_results: Dict[str, int] = {}
    per_portal_errors: Dict[str, str] = {}

    with _LogCapture() as captured:
        with st.status(f" {mode_label} a iniciar...", expanded=True) as status:
            try:
                spider_mgr = SpiderManager()
                raw_total = 0

                #  1. Scraping portal-a-portal 
                n = len(portals)
                for i, portal in enumerate(portals, start=1):
                    status.update(
                        label=f" Scraping {portal} ({i}/{n})...",
                        state="running",
                    )
                    try:
                        results = _run_async(
                            spider_mgr.run_spider(
                                portal,
                                max_pages=max_pages,
                            ),
                        )
                        count = len(results) if results else 0
                        per_portal_results[portal] = count
                        raw_total += count
                        st.write(f"  • `{portal}`: **{count}** anúncios")
                    except Exception as e:  # noqa: BLE001 — surface to UI
                        err_msg = f"{type(e).__name__}: {e}"
                        per_portal_errors[portal] = err_msg
                        per_portal_results[portal] = 0
                        st.write(f"  • `{portal}`:  {err_msg}")
                        logger.error(f"Spider {portal} failed: {err_msg}\n"
                                     f"{traceback.format_exc()}")
                    # Refresh log panel between portals so the user sees movement.
                    _refresh_log_panel(log_placeholder, captured)

                st.write(f"**Scraping concluído:** {raw_total} anúncios brutos no total")

                #  2-4. ETL + Valuation + Scoring 
                counts = _run_pipeline_post_scrape(
                    repo, status, captured, log_placeholder,
                    raw_total, before_total,
                )

                #  Summary 
                new_in_db = counts.get("new_in_db", 0)
                n_failed = len(per_portal_errors)
                final_label = (
                    f" {mode_label} concluído — {new_in_db} novos imóveis na BD"
                    if not n_failed
                    else f" {mode_label} concluído com {n_failed} falha(s) — {new_in_db} novos"
                )
                status.update(label=final_label,
                              state="complete" if not n_failed else "error",
                              expanded=bool(n_failed))

                st.session_state['scraping_message'] = (
                    f" {mode_label} | Brutos: {raw_total} | Novos: {new_in_db} | "
                    f"Duplicados: {counts.get('duplicates', 0)} | "
                    f"Avaliados: {counts.get('valuation', 0)} | "
                    f"Classificados: {counts.get('scoring', 0)} | "
                    f"Falhas: {n_failed}"
                )
                if per_portal_errors:
                    st.markdown("####  Erros por portal")
                    for portal, err in per_portal_errors.items():
                        st.error(f"`{portal}`: {err}")
            except Exception as exc:  # noqa: BLE001
                status.update(label=f" Falhou: {exc}", state="error", expanded=True)
                st.exception(exc)
                _refresh_log_panel(log_placeholder, captured)
                st.session_state['scraping_message'] = f" Erro: {exc}"

    # Persist captured logs for later inspection
    st.session_state['last_scrape_logs'] = captured.text()
    st.session_state['last_per_portal'] = per_portal_results
    st.session_state['last_per_portal_errors'] = per_portal_errors
    st.rerun()


