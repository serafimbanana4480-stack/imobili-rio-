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

from realestate_engine.dashboard.utils.async_helpers import _run_async
from realestate_engine.dashboard.utils.theme import is_dark_mode

# Tail this log file in the UI between stages — written to by loguru via
# realestate_engine.dashboard.__init__ + realestate_engine logging setup.
_LOG_FILE_CANDIDATES: List[Path] = [
    Path(project_root) / "logs" / "app" / "dashboard.log",
    Path(project_root) / "logs" / "engine.log",
    Path(project_root) / "logs" / "app" / "errors.log",
]


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
                st.success(f"{label}\n\n✅ {detail}")
            elif status == "warn":
                st.warning(f"{label}\n\n⚠️ {detail}")
            else:
                st.error(f"{label}\n\n❌ {detail}")
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

    status.update(label="🧹 ETL: normalização + deduplicação...", state="running")
    counts["etl"] = _run_async(PipelineETL().run(batch_size=100000, force_full=True))
    duplicates = max(0, raw_total - counts["etl"])
    st.write(f"**ETL concluído:** {counts['etl']} novos limpos | {duplicates} duplicados")
    _refresh_log_panel(log_placeholder, captured)

    status.update(label="💰 Valuation (estimativa de valor)...", state="running")
    counts["valuation"] = _run_async(ValuationEngine().valuate_batch(batch_size=100000))
    st.write(f"**Valuation:** {counts['valuation']} avaliados")
    _refresh_log_panel(log_placeholder, captured)

    status.update(label="🏆 Scoring (classificação de oportunidade)...", state="running")
    counts["scoring"] = _run_async(ScoringEngine().score_batch(batch_size=100000))
    st.write(f"**Scoring:** {counts['scoring']} classificados")
    _refresh_log_panel(log_placeholder, captured)

    after_total = repo.get_total_clean_listings_count()
    counts["new_in_db"] = max(0, after_total - before_total)
    counts["duplicates"] = duplicates
    return counts


def render_scraping_results():
    """Render scraping results page with final results only."""
    st.title("🔄 Resultados de Scraping")
    st.markdown("*Casas raspadas com preço, valor de mercado e score*")

    repo = DatabaseRepository()

    # ── Quick Links / Shortcuts ───────────────────────────────────────────────
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Ver Overview", use_container_width=True):
            st.session_state['page'] = "🏠 Início"
            st.rerun()
    
    with col2:
        if st.button("🔍 Pesquisa Avançada", use_container_width=True):
            st.session_state['page'] = "🔍 Pesquisar"
            st.rerun()
    
    with col3:
        if st.button("📈 Análise Mercado", use_container_width=True):
            st.session_state['page'] = "📊 Análise"
            st.session_state['analysis_page'] = "📈 Mercado"
            st.rerun()

    st.markdown("---")

    # ── Pre-flight checks (always shown) ───────────────────────────────────
    st.markdown("### 🔍 Pre-flight")
    st.caption("Verificações rápidas antes de executar o pipeline. Bloqueia só se DB falhar.")
    preflight = _preflight_checks(repo)
    can_run = _render_preflight(preflight)

    # ── Run Scraping Buttons ───────────────────────────────────────────────
    st.markdown("### ▶️ Execução")
    col1, col2, col3 = st.columns(3)

    with col1:
        run_full = st.button(
            "▶️ Pipeline Completo",
            type="primary", use_container_width=True,
            disabled=not can_run,
            help="Scraping de todos os portais + ETL + Valuation + Scoring (~10–60min)",
        )
    with col2:
        run_demo = st.button(
            "⚡ Demo Rápido (~30s)",
            use_container_width=True,
            disabled=not can_run,
            help="Apenas casa_sapo_direct (HTTP-only, sem browser) + ETL/Valuation/Scoring",
        )
    with col3:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.session_state['scraping_running'] = False
            st.rerun()

    if run_full or run_demo:
        before_total = repo.get_total_clean_listings_count()
        portals = ["casa_sapo"] if run_demo else list(SpiderManager.DEFAULT_CYCLE_PORTALS)
        mode_label = "Demo Rápido" if run_demo else "Pipeline Completo"

        log_placeholder = st.empty()
        per_portal_results: Dict[str, int] = {}
        per_portal_errors: Dict[str, str] = {}

        with _LogCapture() as captured:
            with st.status(f"🔄 {mode_label} a iniciar...", expanded=True) as status:
                try:
                    spider_mgr = SpiderManager()
                    raw_total = 0

                    # ── 1. Scraping portal-a-portal ──
                    n = len(portals)
                    for i, portal in enumerate(portals, start=1):
                        status.update(
                            label=f"🕷️ Scraping {portal} ({i}/{n})...",
                            state="running",
                        )
                        try:
                            results = _run_async(
                                spider_mgr.run_spider(
                                    portal,
                                    max_pages=1 if run_demo else 20,
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
                            st.write(f"  • `{portal}`: ❌ {err_msg}")
                            logger.error(f"Spider {portal} failed: {err_msg}\n"
                                         f"{traceback.format_exc()}")
                        # Refresh log panel between portals so the user sees movement.
                        _refresh_log_panel(log_placeholder, captured)

                    st.write(f"**Scraping concluído:** {raw_total} anúncios brutos no total")

                    # ── 2-4. ETL + Valuation + Scoring ──
                    counts = _run_pipeline_post_scrape(
                        repo, status, captured, log_placeholder,
                        raw_total, before_total,
                    )

                    # ── Summary ──
                    new_in_db = counts.get("new_in_db", 0)
                    n_failed = len(per_portal_errors)
                    final_label = (
                        f"✅ {mode_label} concluído — {new_in_db} novos imóveis na BD"
                        if not n_failed
                        else f"⚠️ {mode_label} concluído com {n_failed} falha(s) — {new_in_db} novos"
                    )
                    status.update(label=final_label,
                                  state="complete" if not n_failed else "error",
                                  expanded=bool(n_failed))

                    st.session_state['scraping_message'] = (
                        f"✅ {mode_label} | Brutos: {raw_total} | Novos: {new_in_db} | "
                        f"Duplicados: {counts.get('duplicates', 0)} | "
                        f"Avaliados: {counts.get('valuation', 0)} | "
                        f"Classificados: {counts.get('scoring', 0)} | "
                        f"Falhas: {n_failed}"
                    )
                    if per_portal_errors:
                        st.markdown("#### ❌ Erros por portal")
                        for portal, err in per_portal_errors.items():
                            st.error(f"`{portal}`: {err}")
                except Exception as exc:  # noqa: BLE001
                    status.update(label=f"❌ Falhou: {exc}", state="error", expanded=True)
                    st.exception(exc)
                    _refresh_log_panel(log_placeholder, captured)
                    st.session_state['scraping_message'] = f"❌ Erro: {exc}"

        # Persist captured logs for later inspection
        st.session_state['last_scrape_logs'] = captured.text()
        st.session_state['last_per_portal'] = per_portal_results
        st.session_state['last_per_portal_errors'] = per_portal_errors
        st.rerun()

    # ── Pipeline Execution Status ────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⏳ Estado do Pipeline")

    # Show last execution info from DB logs
    recent_jobs = repo.get_recent_job_executions("spider_manager", limit=3)
    if recent_jobs:
        for job in recent_jobs:
            status_emoji = "✅" if job.status == "success" else "❌" if job.status in ("failed", "error") else "⏳"
            st.info(f"{status_emoji} **Scraping** — {job.started_at.strftime('%Y-%m-%d %H:%M') if job.started_at else 'N/A'} — "
                   f"{job.records_processed or 0} registros processados — Status: {job.status.upper()}")
    else:
        st.info("📝 Sem execuções de scraping registadas. O scraping pode ser executado manualmente acima ou automaticamente pelo Orchestrator (24/7).")

    bg = "#1E293B" if is_dark_mode() else "#F8FAFC"
    fg = "#E2E8F0" if is_dark_mode() else "#1E293B"
    border = "#334155" if is_dark_mode() else "#E2E8F0"
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};border-radius:8px;padding:12px;margin-top:8px;color:{fg};">
        <strong>ℹ️ Como funciona:</strong> O scraping é executado automaticamente de hora em hora pelo <code>Orchestrator</code>.
        A dashboard mostra os dados já processados. Para execução manual, use:
        <code>python -m realestate_engine.scheduler.orchestrator</code>
    </div>
    """, unsafe_allow_html=True)

    # ── Show Last Execution Info ───────────────────────────────────────────
    if st.session_state.get('scraping_message'):
        st.success(st.session_state['scraping_message'])
    
    # ── Get Current Data ───────────────────────────────────────────────────
    all_listings = repo.get_clean_listings(limit=10000)
    
    if not all_listings:
        st.warning("⚠️ Nenhum anúncio encontrado na base de dados.")
        st.info("👆 Clique em '▶️ Executar Scraping Completo' para começar.")
        
        # Show helpful info
        st.markdown("---")
        st.subheader("📋 Como Funciona")
        st.markdown("""
        1. **Scraping**: Raspagem de dados dos portais imobiliários (Casa Sapo, ERA, etc.)
        2. **ETL Pipeline**: Normalização, deduplicação, geocodificação e enriquecimento
        3. **Valuation**: Cálculo do valor justo de mercado
        4. **Scoring**: Classificação por oportunidade (Imperdível, Excelente, Bom, etc.)
        
        Após executar o scraping, verá aqui:
        - Total de casas raspadas
        - Preço médio
        - Casas com score alto (Excelentes 7+, Imperdíveis 8+)
        - Tabela detalhada com todas as casas
        """)
        return

    # ── Summary Metrics ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Resumo da Execução")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(all_listings)
    prices = [l.preco_pedido for l in all_listings if l.preco_pedido]
    avg_price = sum(prices) / len(prices) if prices else 0
    
    with col1:
        st.metric("📋 Total Casas", f"{total:,}".replace(",", "."))
    with col2:
        st.metric("💰 Preço Médio", f"{avg_price:,.0f}€".replace(",", "."))
    with col3:
        scores = repo.get_top_scores(min_score=7.0, limit=1000)
        st.metric("⭐ Excelentes (7+)", len(scores))
    with col4:
        top_scores = repo.get_top_scores(min_score=8.0, limit=1000)
        st.metric("🔥 Imperdíveis (8+)", len(top_scores))

    # ── Quick Stats ───────────────────────────────────────────────────────
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    
    portals = set(l.source_portal for l in all_listings)
    freguesias = set(l.freguesia for l in all_listings if l.freguesia)
    
    with col_a:
        st.metric("🌐 Portais", len(portals))
    with col_b:
        st.metric("📍 Freguesias", len(freguesias))
    with col_c:
        st.metric("⏰ Atualizado", datetime.now().strftime("%H:%M"))

    # ── Detailed Results Table ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏠 Casas Raspadas (Detalhado)")

    results_data = []
    for l in all_listings:
        score = repo.get_score_by_listing(l.id)
        vals = getattr(l, "valuations", None)
        val = vals[0] if vals and len(vals) > 0 else None
        
        results_data.append({
            "🏆": score.classificacao if score else "",
            "Score": score.score_total if score else 0,
            "Preço": f"{l.preco_pedido:,.0f}€".replace(",", ".") if l.preco_pedido else "",
            "V. Mercado": f"{val.valor_justo:,.0f}€".replace(",", ".") if val and val.valor_justo else "",
            "Desconto": f"{val.discount*100:+.0f}%" if val and val.discount is not None else "",
            "Portal": l.source_portal,
            "Título": (l.titulo or "")[:50],
            "Área": f"{l.area_util_m2:.0f}m²" if l.area_util_m2 else "",
            "Freguesia": l.freguesia or "",
            "🔗": l.source_url or "",
        })

    df = pd.DataFrame(results_data)
    df = df.sort_values("Score", ascending=False)

    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "🔗": st.column_config.LinkColumn("Link", display_text="Ver"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
        }
    )

    # ── Logs from last run (real, captured) ───────────────────────────────
    if st.session_state.get('last_scrape_logs'):
        with st.expander("📋 Logs da última execução", expanded=False):
            st.code(st.session_state['last_scrape_logs'], language="log")
    else:
        with st.expander("📋 Logs", expanded=False):
            st.caption("Os logs em tempo real aparecem aqui após executar o pipeline.")
