"""Shared extraction helpers used by production spiders.

All helpers are source-agnostic and safe against missing DOM nodes.
No synthetic data is ever produced — missing fields are returned as empty
strings / None so the downstream ETL's validator can reject the listing.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional


AREA_PATTERNS = [
    r"(\d+(?:[.,]\d+)?)\s*m[²2]",
    r"(\d+(?:[.,]\d+)?)\s*sqm",
    r"(\d+(?:[.,]\d+)?)\s*m\b",
]
ROOM_PATTERNS = [
    r"\bT(\d+)\b",
    r"(\d+)\s*quartos?",
    r"(\d+)\s*bedrooms?",
]
PRICE_PATTERNS = [
    r"(\d[\d\s.,]*)\s*€",
    r"€\s*(\d[\d\s.,]*)",
    r"(\d[\d\s.,]*)\s*EUR",
]


class ExtractionMixin:
    """Shared helpers; intended to be combined with BaseSpiderNodriver."""

    # ── Cookies (common CMP vendors) ───────────────────────────────────
    COOKIE_SELECTORS: List[str] = [
        "#didomi-notice-agree-button",
        "#onetrust-accept-btn-handler",
        'button[aria-label*="accept" i]',
        'button[aria-label*="aceitar" i]',
        'button[id*="accept" i]',
        'button[class*="accept" i]',
        'button[data-testid*="accept" i]',
        '[class*="cookie"] button',
    ]

    async def accept_cookies(self) -> None:
        for sel in self.COOKIE_SELECTORS:
            try:
                clicked = await self.safe_evaluate(
                    f"(() => {{ const el = document.querySelector({sel!r}); "
                    f"  if (el) {{ el.click(); return true; }} return false; }})()",
                    timeout=3.0,
                )
                if clicked:
                    import asyncio
                    await asyncio.sleep(1)
                    break
            except Exception:
                continue

    # ── JSON-LD extraction (schema.org Product / Offer / RealEstateListing) ──
    async def extract_jsonld(self) -> List[Dict]:
        """Return flattened JSON-LD entities present in the page."""
        script = """
        (() => {
            const out = [];
            const walk = (node) => {
                if (Array.isArray(node)) { node.forEach(walk); return; }
                if (node && typeof node === 'object') {
                    out.push(node);
                    if (node['@graph']) walk(node['@graph']);
                    if (node.itemListElement) walk(node.itemListElement);
                    if (node.mainEntity) walk(node.mainEntity);
                }
            };
            document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
                try { walk(JSON.parse(s.innerText)); } catch (e) {}
            });
            return out;
        })()
        """
        try:
            result = await self.safe_evaluate(script, timeout=10.0)
            return result or []
        except Exception:
            return []

    # ── Text helpers ───────────────────────────────────────────────────
    @staticmethod
    def extract_area_text(text: str) -> str:
        if not text:
            return ""
        for pat in AREA_PATTERNS:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return ""

    @staticmethod
    def extract_rooms_text(text: str) -> str:
        if not text:
            return ""
        for pat in ROOM_PATTERNS:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return ""

    @staticmethod
    def extract_price_text(text: str) -> str:
        if not text:
            return ""
        for pat in PRICE_PATTERNS:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return ""

    # ── Source ID derivation ───────────────────────────────────────────
    @staticmethod
    def derive_source_id(url: str) -> str:
        """Derive a stable source_id from a listing URL.

        Tries to pick the last significant numeric chunk; falls back to the
        last path segment.
        """
        if not url:
            return ""
        # Numeric chunk >= 4 digits is the most common listing id pattern
        nums = re.findall(r"\d{4,}", url)
        if nums:
            return nums[-1]
        tail = url.rstrip("/").split("/")[-1]
        return tail or url
