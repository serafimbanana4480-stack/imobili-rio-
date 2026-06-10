"""Real-world free-proxy test harness.

End-to-end, no-mocks test of the free-proxy pipeline:

    1. Fetch raw proxies from the configured free-proxy sources.
    2. Validate them with ``ProxyValidator`` (echo + optional target).
    3. For each real-estate portal, issue N probe requests and record
       success / block / error counts + latency.
    4. Emit an honest performance report (JSON + Markdown).

Usage (from repo root):
    py -3 scripts/test_free_proxies.py
    py -3 scripts/test_free_proxies.py --validate 300 --probes 5

The script ONLY does network I/O. It does not touch the database or
the pipeline. If the network is unavailable or every free proxy is
dead, the report will say so — nothing will be faked.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Ensure repo root is on sys.path when invoked as ``py scripts/test_free_proxies.py``.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger

from realestate_engine.scraping.free_proxy_provider import FreeProxyProvider
from realestate_engine.scraping.http_client import SmartHttpClient
from realestate_engine.scraping.proxy_manager import PORTAL_STRATEGY, ProxyEntry, ProxyManager
from realestate_engine.scraping.proxy_validator import ProxyValidator


# Lightweight probe URLs per portal — chosen to minimise bandwidth while
# still triggering the same anti-bot stack as the real scrapers.
PROBE_URLS: Dict[str, str] = {
    "imovirtual": "https://www.imovirtual.com/pt/resultados/comprar/apartamento/porto",
    "idealista":  "https://www.idealista.pt/comprar-casas/porto-porto/",
    "casa_sapo":  "https://casa.sapo.pt/comprar/apartamentos/porto/",
    "era":        "https://www.era.pt/comprar/apartamentos/porto",
    "remax":      "https://www.remax.pt/comprar/porto",
    "supercasa":  "https://supercasa.pt/comprar/apartamentos/porto",
    "century21":  "https://www.century21.pt/comprar/imoveis/porto",
    "olx":        "https://www.olx.pt/imoveis/apartamentos/porto/",
}


async def step_fetch_and_validate(
    max_validate: int,
    target_url: Optional[str],
) -> tuple[list, "object"]:
    provider = FreeProxyProvider()
    raw = await provider.fetch_all()
    if not raw:
        logger.error("No raw proxies fetched — aborting")
        return [], None

    sample = raw[:max_validate]
    validator = ProxyValidator(target_url=target_url, max_concurrent=40)
    pool = await validator.validate_batch(sample)
    return raw, pool


def build_manager_with_pool(usable_checks) -> ProxyManager:
    mgr = ProxyManager(load_cache=False)
    # Clear anything auto-loaded from env (we want a clean, reproducible run).
    mgr.entries = {}
    for check in usable_checks:
        url = check.proxy.url
        mgr.entries[url] = ProxyEntry(
            url=url, source=f"free:{check.proxy.source}",
            latency_ms=check.latency_ms, success=1,
        )
    return mgr


async def probe_portal(mgr: ProxyManager, portal: str, url: str, probes: int) -> dict:
    """Run ``probes`` sequential requests against ``url``; return stats."""
    client = SmartHttpClient(portal=portal, proxy_manager=mgr, max_retries=2)
    stats = {
        "portal": portal,
        "strategy": ProxyManager.strategy_for(portal),
        "probes": probes,
        "success": 0,
        "blocked": 0,
        "errors": 0,
        "latency_ms_sum": 0.0,
        "latency_ms_count": 0,
        "sample_status": [],
        "sample_errors": [],
    }

    for i in range(probes):
        result = await client.fetch(url)
        stats["sample_status"].append(result.status_code)
        if result.ok:
            stats["success"] += 1
            stats["latency_ms_sum"] += result.latency_ms
            stats["latency_ms_count"] += 1
        elif result.error and ("blocked" in result.error or result.error.startswith("http_")):
            stats["blocked"] += 1
            stats["sample_errors"].append(result.error)
        else:
            stats["errors"] += 1
            stats["sample_errors"].append(result.error or "unknown")

    success_rate = stats["success"] / probes if probes else 0.0
    avg_latency = (
        stats["latency_ms_sum"] / stats["latency_ms_count"]
        if stats["latency_ms_count"] else None
    )
    stats["success_rate"] = round(success_rate, 3)
    stats["avg_latency_ms"] = round(avg_latency, 1) if avg_latency is not None else None
    return stats


def render_markdown_report(raw_count: int, pool_summary: dict, per_portal: List[dict]) -> str:
    lines: list[str] = []
    lines.append("# Free Proxy — Real Test Report")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    lines.append("")
    lines.append("## 1. Proxy Pool")
    lines.append("")
    lines.append(f"- Raw proxies fetched: **{raw_count}**")
    if pool_summary:
        lines.append(f"- Working (fast): **{pool_summary.get('working', 0)}**")
        lines.append(f"- Slow but usable: **{pool_summary.get('slow', 0)}**")
        lines.append(f"- Dead / blocked: **{pool_summary.get('dead', 0)}**")
        avg = pool_summary.get("avg_latency_ms_working")
        if avg is not None:
            lines.append(f"- Avg latency (working): **{avg} ms**")
    lines.append("")
    lines.append("## 2. Per-Portal Results")
    lines.append("")
    lines.append("| Portal | Strategy | Probes | Success | Blocked | Errors | Success Rate | Avg Latency |")
    lines.append("|--------|----------|--------|---------|---------|--------|--------------|-------------|")
    for s in per_portal:
        lines.append(
            f"| {s['portal']} | {s['strategy']} | {s['probes']} | "
            f"{s['success']} | {s['blocked']} | {s['errors']} | "
            f"{round(s['success_rate'] * 100, 1)}% | "
            f"{(str(s['avg_latency_ms']) + ' ms') if s['avg_latency_ms'] is not None else '—'} |"
        )
    lines.append("")
    lines.append("## 3. Notes")
    lines.append("")
    lines.append("- `strategy=direct` means no proxy is ever used for that portal.")
    lines.append("- `strategy=hybrid` means direct is tried first; proxies are used as fallback.")
    lines.append("- `strategy=proxy` means every request goes through a proxy.")
    lines.append("- Low success rates on heavily-protected portals (Idealista, OLX) are **expected** with free proxies.")
    lines.append("")
    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

    report_dir = ROOT / "logs"
    report_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    logger.info("=== STAGE 1: fetch + validate free proxies ===")
    raw, pool = await step_fetch_and_validate(
        max_validate=args.validate,
        target_url=args.target_validate or None,
    )
    raw_count = len(raw)
    if pool is None or not pool.usable():
        logger.warning("No usable proxies after validation — portal tests will run direct-only")
        usable = []
    else:
        usable = pool.usable()[: args.max_accept]
        logger.info(f"Accepted {len(usable)} usable proxies (of {len(pool.working)} fast + {len(pool.slow)} slow)")

    mgr = build_manager_with_pool(usable)

    logger.info("=== STAGE 2: probe each portal ===")
    portals = args.portals or list(PROBE_URLS.keys())
    per_portal: List[dict] = []
    for portal in portals:
        url = PROBE_URLS.get(portal)
        if not url:
            logger.warning(f"Unknown portal {portal}; skipping")
            continue
        logger.info(f"--- probing {portal} ({ProxyManager.strategy_for(portal)}) ---")
        stats = await probe_portal(mgr, portal, url, probes=args.probes)
        logger.info(
            f"{portal}: success={stats['success']}/{stats['probes']} "
            f"blocked={stats['blocked']} errors={stats['errors']} "
            f"avg_latency={stats['avg_latency_ms']} ms"
        )
        per_portal.append(stats)

    pool_summary = pool.summary() if pool is not None else {}
    elapsed = round(time.time() - started, 1)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_seconds": elapsed,
        "raw_proxies_fetched": raw_count,
        "pool_summary": pool_summary,
        "per_portal": per_portal,
        "portal_strategy": PORTAL_STRATEGY,
    }

    json_path = report_dir / "free_proxy_report.json"
    md_path = report_dir / "free_proxy_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(raw_count, pool_summary, per_portal), encoding="utf-8")

    logger.info(f"Report written: {md_path}")
    logger.info(f"JSON:          {json_path}")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Real-world free-proxy test harness")
    p.add_argument("--validate", type=int, default=250,
                   help="Max raw proxies to validate (cap for speed)")
    p.add_argument("--max-accept", type=int, default=40,
                   help="Max validated proxies to load into the pool")
    p.add_argument("--probes", type=int, default=3,
                   help="Probe requests per portal")
    p.add_argument("--target-validate", default="",
                   help="Optional target URL checked during validation (e.g. idealista robots.txt)")
    p.add_argument("--portals", nargs="*", default=None,
                   help="Subset of portals to test (default: all)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(asyncio.run(main_async(args)))
