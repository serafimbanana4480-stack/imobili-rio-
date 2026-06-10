"""Migration script: SQLite → PostgreSQL (FASE 6).

Prerequisites:
  docker compose up -d postgres
  pip install psycopg2-binary

Usage:
  python -m realestate_engine.infrastructure.migrate_to_postgres
"""
import os
import sqlite3
from typing import List, Dict, Any
from loguru import logger

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    logger.error("psycopg2-binary is required. Install: pip install psycopg2-binary")
    raise

# Mapping of SQLite tables to PostgreSQL tables
TABLES = [
    "raw_listings",
    "clean_listings",
    "valuations",
    "scores",
    "price_history",
    "notifications",
    "watchlist",
    "job_execution_log",
    "ine_data",
    "config",
]


def get_sqlite_rows(db_path: str, table: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def migrate_table(sqlite_path: str, pg_dsn: str, table: str, batch_size: int = 500):
    rows = get_sqlite_rows(sqlite_path, table)
    if not rows:
        logger.info(f"Table {table}: no rows to migrate")
        return

    # Get columns from first row
    columns = list(rows[0].keys())
    # Exclude 'id' if it's a UUID primary key — let PostgreSQL generate or preserve
    col_str = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("%s" for _ in columns)

    conn = psycopg2.connect(pg_dsn)
    cur = conn.cursor()

    # Truncate and load pattern (or use ON CONFLICT for upserts)
    cur.execute(f"TRUNCATE TABLE {table} CASCADE")

    # Batch insert with execute_values for performance
    values = [tuple(row.get(c) for c in columns) for row in rows]
    execute_values(
        cur,
        f"INSERT INTO {table} ({col_str}) VALUES %s",
        values,
        page_size=batch_size,
    )

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Table {table}: migrated {len(rows)} rows")


def run_migration(sqlite_path: str = None, pg_dsn: str = None):
    sqlite_path = sqlite_path or os.getenv("SQLITE_DB", "data/db/realestate.db")
    pg_dsn = pg_dsn or os.getenv(
        "POSTGRES_DSN", "postgresql://realestate:realestate_secure_2026@localhost:5432/realestate")

    logger.info(f"Starting migration from {sqlite_path} to PostgreSQL")
    for table in TABLES:
        try:
            migrate_table(sqlite_path, pg_dsn, table)
        except Exception as e:
            logger.error(f"Migration failed for {table}: {e}")
    logger.info("Migration complete")


if __name__ == "__main__":
    run_migration()
