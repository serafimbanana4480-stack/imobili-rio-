"""Quick DB status dump — used by verification runs."""
import sqlite3, sys, pathlib
db = pathlib.Path("data/db/realestate.db")
if not db.exists():
    print(f"DB not found: {db}"); sys.exit(1)
c = sqlite3.connect(str(db)); cur = c.cursor()
tables = ["raw_listings","clean_listings","valuations","scores","price_history","notifications","job_execution_log"]
print("=== row counts ===")
for t in tables:
    try: print(f"  {t:25s} {cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    except Exception as e: print(f"  {t:25s} ERR {e}")
print("\n=== raw_listings per portal ===")
for row in cur.execute("SELECT source_portal, COUNT(*) FROM raw_listings GROUP BY source_portal ORDER BY 2 DESC"):
    print(f"  {row[0]:15s} {row[1]}")
print("\n=== last 10 jobs ===")
cols = [r[1] for r in cur.execute("PRAGMA table_info(job_execution_log)")]
ts_col = next((c for c in cols if "time" in c.lower() or "start" in c.lower()), "id")
for row in cur.execute(f"SELECT job_name, status, records_processed, {ts_col} FROM job_execution_log ORDER BY id DESC LIMIT 10"):
    print(f"  {row[3]} | {row[1]:7s} | {(row[2] or 0):6d} | {row[0]}")
print("\n=== latest raw per portal ===")
for row in cur.execute("SELECT source_portal, MAX(scrape_timestamp) FROM raw_listings GROUP BY source_portal"):
    print(f"  {row[0]:15s} {row[1]}")
