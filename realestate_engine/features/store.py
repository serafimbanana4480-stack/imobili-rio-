"""Feature Store base for ML feature versioning and reuse."""
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class FeatureSet:
    name: str
    version: str
    features: Dict[str, Any]
    source: str
    computed_at: str
    metadata: Dict = field(default_factory=dict)


class FeatureStore:
    def __init__(self, db_path: str = "data/db/feature_store.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                version TEXT,
                features TEXT,
                source TEXT,
                computed_at TEXT,
                metadata TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_registry (
                name TEXT PRIMARY KEY,
                latest_version TEXT,
                description TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_feature_set(self, feature_set: FeatureSet):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feature_sets (name, version, features, source, computed_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            feature_set.name,
            feature_set.version,
            json.dumps(feature_set.features, default=str),
            feature_set.source,
            feature_set.computed_at,
            json.dumps(feature_set.metadata),
        ))
        cursor.execute("""
            INSERT OR REPLACE INTO feature_registry (name, latest_version, description, updated_at)
            VALUES (?, ?, ?, ?)
        """, (
            feature_set.name,
            feature_set.version,
            feature_set.metadata.get("description", ""),
            datetime.now(UTC).isoformat(),
        ))
        conn.commit()
        conn.close()
        logger.info(f"FeatureStore: saved {feature_set.name} v{feature_set.version}")

    def get_feature_set(self, name: str, version: Optional[str] = None) -> Optional[FeatureSet]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if version:
            cursor.execute("""
                SELECT name, version, features, source, computed_at, metadata
                FROM feature_sets WHERE name = ? AND version = ? ORDER BY computed_at DESC LIMIT 1
            """, (name, version))
        else:
            cursor.execute("""
                SELECT name, version, features, source, computed_at, metadata
                FROM feature_sets WHERE name = ? ORDER BY computed_at DESC LIMIT 1
            """, (name,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return FeatureSet(
            name=row[0],
            version=row[1],
            features=json.loads(row[2]),
            source=row[3],
            computed_at=row[4],
            metadata=json.loads(row[5]) if row[5] else {},
        )

    def list_versions(self, name: str) -> List[str]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT version FROM feature_sets WHERE name = ? ORDER BY computed_at DESC
        """, (name,))
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]
