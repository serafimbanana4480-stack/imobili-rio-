"""Detail-page scraper — extracts energy cert, year built, condition from listing pages.

Usage:
    python scripts/run_detail_scraping.py [--batch-size 20] [--max-listings 100]

Strategy:
- Casa Sapo / REMAX: direct HTTP (no proxy needed)
- Imovirtual: requires proxy (skipped if RESIDENTIAL_PROXY_URL is empty)
- Resumable: SQLite progress tracking
- Batch processing with delays
"""
import sys, os, asyncio, re, json, time, argparse
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "realestate_engine"))

import httpx
from loguru import logger
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import CleanListing, RawListing
from realestate_engine.scraping.proxy_manager import ProxyManager

Base = declarative_base()

class DetailScrapingProgress(Base):
    __tablename__ = "detail_scraping_progress"
    id = Column(Integer, primary_key=True)
    source_portal = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, success, failed, skipped
    last_attempt = Column(DateTime, default=datetime.utcnow)
    extracted_fields = Column(String, default="")  # JSON of extracted fields

# --- Extraction helpers -------------------------------------------------

LD_JSON_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

ENERGY_RE = re.compile(
    r'certificado\s+energ[eé]tico[^>]*>\s*([^<\n]{1,30})',
    re.IGNORECASE,
)
YEAR_RE = re.compile(
    r'(?:ano\s+de\s+constru[cç][aã]o|constru[cç][aã]o|ano)\s*[:\-]?\s*(\d{4})',
    re.IGNORECASE,
)
CONDITION_RE = re.compile(
    r'(?:estado\s+de\s+conserva[cç][aã]o|estado|condi[cç][aã]o)\s*[:\-]?\s*([^<\n]{2,40})',
    re.IGNORECASE,
)

def _extract_json_ld(text: str) -> List[Dict]:
    results = []
    for block in LD_JSON_RE.findall(text):
        raw = block.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if isinstance(node, dict):
                results.append(node)
    return results

def _walk_dict(data: Any, key_fragments: List[str]) -> Optional[str]:
    """Walk nested dicts looking for keys containing any of the fragments."""
    if isinstance(data, dict):
        for k, v in data.items():
            if any(frag in k.lower() for frag in key_fragments):
                if isinstance(v, str):
                    return v
                if isinstance(v, (int, float)):
                    return str(v)
            result = _walk_dict(v, key_fragments)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _walk_dict(item, key_fragments)
            if result:
                return result
    return None

def _extract_from_json_ld(html_text: str) -> Dict[str, Optional[str]]:
    """Try to extract energy cert / year / condition from JSON-LD blocks."""
    nodes = _extract_json_ld(html_text)
    energy = _walk_dict(nodes, ["energy", "energ", "certificado", "cee"])
    year = _walk_dict(nodes, ["year", "ano", "construcao", "build"])
    condition = _walk_dict(nodes, ["condition", "estado", "conservacao", "state"])
    # Clean year to just digits
    if year:
        m = re.search(r'(\d{4})', str(year))
        year = m.group(1) if m else None
    return {
        "energy_cert": energy.strip() if energy else None,
        "year_built": int(year) if year and year.isdigit() else None,
        "condition": condition.strip() if condition else None,
    }

def _extract_from_regex(html_text: str) -> Dict[str, Optional[str]]:
    """Fallback regex extraction from raw HTML."""
    energy_m = ENERGY_RE.search(html_text)
    year_m = YEAR_RE.search(html_text)
    condition_m = CONDITION_RE.search(html_text)
    return {
        "energy_cert": energy_m.group(1).strip() if energy_m else None,
        "year_built": int(year_m.group(1)) if year_m else None,
        "condition": condition_m.group(1).strip() if condition_m else None,
    }

def _extract_all(html_text: str) -> Dict[str, Optional[str]]:
    """Combine JSON-LD + regex extraction."""
    result = _extract_from_json_ld(html_text)
    fallback = _extract_from_regex(html_text)
    # Merge: prefer JSON-LD, fallback to regex
    for k in result:
        if not result[k] and fallback.get(k):
            result[k] = fallback[k]
    return result

# --- Scraping logic -----------------------------------------------------

async def fetch_detail_page(
    client: httpx.AsyncClient,
    url: str,
    proxy_url: Optional[str] = None,
    delay: float = 1.5,
) -> Optional[str]:
    """Fetch a detail page and return HTML text."""
    await asyncio.sleep(delay)
    proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
    try:
        resp = await client.get(url, proxies=proxies, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited on {url[:80]}, waiting {retry_after}s")
            await asyncio.sleep(retry_after)
            return None
        else:
            logger.debug(f"HTTP {resp.status_code} for {url[:80]}")
            return None
    except Exception as e:
        logger.debug(f"Fetch error for {url[:80]}: {e}")
        return None

def update_progress(session, portal: str, source_id: str, status: str, fields: Dict):
    """Upsert progress record."""
    rec = session.query(DetailScrapingProgress).filter_by(
        source_portal=portal, source_id=source_id
    ).first()
    if not rec:
        rec = DetailScrapingProgress(
            source_portal=portal,
            source_id=source_id,
            status=status,
            extracted_fields=json.dumps(fields, default=str),
        )
        session.add(rec)
    else:
        rec.status = status
        rec.last_attempt = datetime.utcnow()
        rec.extracted_fields = json.dumps(fields, default=str)
    session.commit()

def _build_url(listing: CleanListing) -> Optional[str]:
    """Construct detail page URL from available data."""
    if listing.source_url:
        return listing.source_url
    if not listing.source_id:
        return None
    if listing.source_portal == "casa_sapo":
        return f"https://casa.sapo.pt/p{listing.source_id}"
    if listing.source_portal == "remax":
        # REMAX URLs need city/neighbourhood which we don't have reliably
        return None
    if listing.source_portal == "imovirtual":
        # Imovirtual URLs need slug; source_id alone isn't enough
        return None
    return None

def get_pending_listings(repo_session, progress_session, portal: str, max_n: int):
    """Get listings missing fields, excluding already processed."""
    # Already processed IDs
    done = {
        r.source_id for r in progress_session.query(DetailScrapingProgress)
        .filter(DetailScrapingProgress.source_portal == portal)
        .filter(DetailScrapingProgress.status.in_(["success", "failed", "skipped"]))
        .all()
    }
    listings = repo_session.query(CleanListing).filter(
        CleanListing.source_portal == portal,
    ).filter(
        (CleanListing.cert_energetico == None) | (CleanListing.cert_energetico == "") |
        (CleanListing.ano_construcao == None) |
        (CleanListing.estado == None) | (CleanListing.estado == "")
    ).limit(max_n * 3).all()  # fetch extra in case many are already done

    # Only include listings where we can construct or have a URL
    pending = [l for l in listings if l.source_id and l.source_id not in done and _build_url(l)]
    return pending[:max_n]

async def process_portal(
    repo_session,
    progress_session,
    portal: str,
    proxy_url: Optional[str],
    batch_size: int,
    client: httpx.AsyncClient,
):
    """Process one portal batch."""
    listings = get_pending_listings(repo_session, progress_session, portal, batch_size)
    if not listings:
        logger.info(f"[{portal}] No pending listings")
        return 0, 0

    logger.info(f"[{portal}] Processing {len(listings)} listings")
    success = 0
    for i, listing in enumerate(listings):
        url = _build_url(listing)
        if not url:
            update_progress(progress_session, portal, listing.source_id, "skipped", {"reason": "no_url"})
            continue

        # Skip Imovirtual if no proxy
        if portal == "imovirtual" and not proxy_url:
            update_progress(progress_session, portal, listing.source_id, "skipped", {"reason": "no_proxy"})
            continue

        html = await fetch_detail_page(client, url, proxy_url, delay=1.0 + i * 0.1)
        if not html:
            update_progress(progress_session, portal, listing.source_id, "failed", {})
            continue

        fields = _extract_all(html)
        extracted_any = bool(fields.get("energy_cert") or fields.get("year_built") or fields.get("condition"))

        if extracted_any:
            # Update CleanListing
            if fields.get("energy_cert"):
                listing.cert_energetico = fields["energy_cert"]
            if fields.get("year_built"):
                listing.ano_construcao = fields["year_built"]
            if fields.get("condition"):
                listing.estado = fields["condition"]

            # Also update RawListing.raw_data for future ETL runs
            raw = repo_session.query(RawListing).filter_by(
                source_portal=portal, source_id=listing.source_id
            ).first()
            if raw and raw.raw_data:
                raw.raw_data["energy_cert"] = fields.get("energy_cert")
                raw.raw_data["year_built"] = fields.get("year_built")
                raw.raw_data["condition"] = fields.get("condition")

            repo_session.commit()
            success += 1

        update_progress(progress_session, portal, listing.source_id, "success" if extracted_any else "success_no_data", fields)
        logger.info(f"[{portal}] {listing.source_id}: energy={fields.get('energy_cert')}, year={fields.get('year_built')}, condition={fields.get('condition')}")

    return success, len(listings)

async def main():
    parser = argparse.ArgumentParser(description="Detail-page scraper for missing fields")
    parser.add_argument("--batch-size", type=int, default=20, help="Listings per portal per run")
    parser.add_argument("--max-listings", type=int, default=100, help="Max total listings to process")
    parser.add_argument("--portals", default="casa_sapo,remax,imovirtual", help="Comma-separated portals")
    args = parser.parse_args()

    logger.add(sys.stderr, level="INFO")

    # Setup progress DB (SQLite alongside main DB)
    progress_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "db", "detail_scraping_progress.db")
    os.makedirs(os.path.dirname(progress_db_path), exist_ok=True)
    progress_engine = create_engine(f"sqlite:///{progress_db_path}")
    Base.metadata.create_all(progress_engine)
    ProgressSession = sessionmaker(bind=progress_engine)

    repo = DatabaseRepository()
    proxy_mgr = ProxyManager()
    proxy_url = proxy_mgr.get_proxy()  # may be None

    portals = [p.strip() for p in args.portals.split(",")]
    total_success = 0
    total_processed = 0

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
        timeout=30,
    ) as client:
        for portal in portals:
            if total_processed >= args.max_listings:
                break
            with repo.Session() as repo_session:
                with ProgressSession() as progress_session:
                    s, n = await process_portal(
                        repo_session, progress_session, portal, proxy_url,
                        args.batch_size, client,
                    )
                    total_success += s
                    total_processed += n

    logger.info(f"Done. Processed {total_processed} listings, extracted data from {total_success}.")

if __name__ == "__main__":
    asyncio.run(main())
