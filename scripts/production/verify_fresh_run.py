"""Print a one-line summary of the current DB state after a pipeline run.

Used by ``run_scrapers.bat`` and CI smoke checks. Exits non-zero if the
``clean_listings`` table is empty, which makes the batch script surface
failures loudly instead of silently reporting success on an empty DB.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.database.repository import DatabaseRepository


def main() -> int:
    repo = DatabaseRepository()
    # Sample-data guard — will raise if any is_sample=1 rows exist
    try:
        repo.assert_no_sample_data()
    except Exception as exc:  # noqa: BLE001
        print(f"[verify] PURITY GUARD FAILED: {exc}")
        return 2

    raw = repo.get_raw_listings(limit=100000)
    clean = repo.get_clean_listings(limit=100000)
    scored = repo.get_top_scores(min_score=0.0, limit=100000)
    valued = sum(1 for c in clean if c.valuations)

    print(
        "[verify] Raw: {raw} | Clean: {clean} | Valued: {valued} | Scored: {scored}".format(
            raw=len(raw),
            clean=len(clean),
            valued=valued,
            scored=len(scored),
        )
    )

    if not clean:
        print("[verify] FAIL: clean_listings is empty — pipeline produced no usable data.")
        return 1
    if len(clean) < 500:
        print(
            f"[verify] WARN: clean_listings below success bar "
            f"({len(clean)}/500). Pipeline ran but under-delivered."
        )
        return 0
    print(f"[verify] PASS: success bar met ({len(clean)} >= 500 clean listings).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
