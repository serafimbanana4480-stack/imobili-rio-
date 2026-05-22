"""Integration test: live fetch of Imovirtual via __NEXT_DATA__.

Marked ``online`` so CI without internet skips it. Validates that:

* the search page yields a populated ``__NEXT_DATA__`` block
* at least 30 items per page get projected into the pipeline's raw format
* core fields (price, area, rooms) are always present
* morada_raw resolves to a non-empty address string
"""
from __future__ import annotations

import asyncio

import pytest

from realestate_engine.scraping.spiders.imovirtual_nextdata_spider import (
    ImovirtualNextDataSpider,
)


@pytest.mark.online
def test_imovirtual_nextdata_single_page_yields_full_records():
    spider = ImovirtualNextDataSpider()
    results = asyncio.run(spider.run(max_pages=1))

    assert len(results) >= 30, (
        f"expected at least 30 listings on a single Porto search page, got {len(results)}"
    )

    for r in results:
        raw = r["raw_data"]
        assert r["source_portal"] == "imovirtual"
        assert r["source_id"], "source_id must be populated"
        assert r["source_url"].startswith("https://www.imovirtual.com/pt/"), r["source_url"]
        assert raw["price"] and raw["price"] > 0
        assert raw["area"] and raw["area"] > 0
        assert raw["rooms"] is not None and raw["rooms"] >= 0
        assert raw["morada_raw"], "address must be reconstructed from reverseGeocoding"
        # fingerprint-critical fields
        assert raw["distrito"]
