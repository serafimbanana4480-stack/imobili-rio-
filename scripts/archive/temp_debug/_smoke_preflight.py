"""Smoke-test the dashboard scraping page helpers without launching Streamlit.

Run: ``venv312\\Scripts\\python.exe scripts\\debug\\_smoke_preflight.py``
"""
from realestate_engine.dashboard.views.scraping_results import (
    _preflight_checks,
    _tail_log_file,
)
from realestate_engine.database.repository import DatabaseRepository


def main() -> int:
    print("--- Pre-flight ---")
    results = _preflight_checks(DatabaseRepository())
    for name, info in results.items():
        status = info["status"]
        detail = info["detail"]
        print(f"  {name:8s} [{status:5s}] {detail}")

    print()
    print("--- Tail log (last 5 lines) ---")
    tail = _tail_log_file(lines=5)
    print(tail or "(no log file found)")

    # Non-zero exit only if DB blocked the pipeline.
    return 0 if results.get("DB", {}).get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
