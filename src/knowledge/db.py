"""SQLite database manager for ORBIT knowledge and discovery storage."""

import sqlite3
import os
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

DEFAULT_DB_PATH = os.getenv("ORBIT_DB_PATH", "data/orbit.db")


@contextmanager
def get_db(db_path: str = DEFAULT_DB_PATH):
    """Context manager returning a connection with WAL mode enabled, closed on exit."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize core tables if they do not exist."""
    with get_db(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                published TEXT,
                raw_text TEXT,
                summary TEXT,
                fetched_at TEXT NOT NULL,
                source_name TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                status TEXT DEFAULT 'fetched',
                cluster_id INTEGER,
                novelty_score REAL
            );
        """)
        # Safe migration if table previously existed without new columns
        for col, col_type in [("cluster_id", "INTEGER"), ("novelty_score", "REAL")]:
            try:
                conn.execute(f"ALTER TABLE sources ADD COLUMN {col} {col_type};")
            except sqlite3.OperationalError:
                pass  # column already exists

        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_hash ON sources(content_hash);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_published ON sources(published);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_cluster ON sources(cluster_id);")

        # Knowledge Graph Nodes: Entities
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(canonical_name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);")

        # Knowledge Graph Edges: Relations with Source Evidence Provenance
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity_id INTEGER NOT NULL REFERENCES entities(id),
                target_entity_id INTEGER NOT NULL REFERENCES entities(id),
                relation_type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                occurred_at TEXT,
                UNIQUE(source_entity_id, target_entity_id, relation_type, source_id)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_entity_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_entity_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_provenance ON relations(source_id);")


def insert_source(
    url: str,
    title: str,
    published: Optional[str],
    raw_text: str,
    summary: str,
    fetched_at: str,
    source_name: str,
    content_hash: str,
    status: str = "fetched",
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[int]:
    """Insert a source record. Returns row id if inserted, None if duplicate url or hash exists."""
    with get_db(db_path) as conn:
        # Check URL or content hash duplicates
        cur = conn.execute(
            "SELECT id FROM sources WHERE url = ? OR content_hash = ? LIMIT 1",
            (url, content_hash),
        )
        if cur.fetchone():
            return None

        cur = conn.execute(
            """
            INSERT INTO sources (url, title, published, raw_text, summary, fetched_at, source_name, content_hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (url, title, published, raw_text, summary, fetched_at, source_name, content_hash, status),
        )
        conn.commit()
        return cur.lastrowid


def get_source_count(db_path: str = DEFAULT_DB_PATH) -> int:
    """Get total number of collected sources."""
    with get_db(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM sources")
        return cur.fetchone()[0]


def get_source_by_id(source_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a single discovery source by ID."""
    with get_db(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM sources WHERE id = ? LIMIT 1",
            (source_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_sources_by_cluster(cluster_id: int, limit: int = 10, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all discovery sources sharing a cluster."""
    with get_db(db_path) as conn:
        cur = conn.execute(
            "SELECT id, url, title, published, summary, source_name, fetched_at, novelty_score FROM sources WHERE cluster_id = ? ORDER BY id DESC LIMIT ?",
            (cluster_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]


def get_latest_sources(limit: int = 20, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve latest discoveries from the database."""
    with get_db(db_path) as conn:
        cur = conn.execute(
            "SELECT id, url, title, published, summary, source_name, fetched_at, status, content_hash FROM sources ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_recent_titles(limit: int = 500, db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """Retrieve list of recent titles for fast novelty scoring."""
    with get_db(db_path) as conn:
        cur = conn.execute("SELECT title FROM sources ORDER BY id DESC LIMIT ?", (limit,))
        return [row[0] for row in cur.fetchall()]


def get_source_stats(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve breakdown of counts and last fetch time by source."""
    with get_db(db_path) as conn:
        cur = conn.execute("""
            SELECT 
                source_name, 
                COUNT(*) as count, 
                MAX(fetched_at) as last_seen
            FROM sources 
            GROUP BY source_name 
            ORDER BY count DESC
        """)
        return [dict(row) for row in cur.fetchall()]


def update_source_clusters(
    updates: List[Tuple[int, float, int]], db_path: str = DEFAULT_DB_PATH
) -> None:
    """Batch update (cluster_id, novelty_score) where id = ?."""
    init_db(db_path)
    with get_db(db_path) as conn:
        conn.executemany(
            "UPDATE sources SET cluster_id = ?, novelty_score = ? WHERE id = ?",
            updates,
        )
        conn.commit()


def get_all_sources_for_clustering(
    limit: int = 500, db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Fetch recent sources to cluster."""
    with get_db(db_path) as conn:
        cur = conn.execute(
            "SELECT id, url, title, published, summary, source_name, fetched_at FROM sources ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_topic_clusters(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Get active topic clusters and member counts."""
    with get_db(db_path) as conn:
        cur = conn.execute("""
            SELECT 
                cluster_id, 
                COUNT(*) as item_count, 
                MIN(title) as sample_title,
                MAX(published) as latest_activity,
                AVG(novelty_score) as avg_novelty
            FROM sources 
            WHERE cluster_id IS NOT NULL 
            GROUP BY cluster_id 
            ORDER BY item_count DESC, latest_activity DESC
        """)
        return [dict(row) for row in cur.fetchall()]


def upsert_entity(
    canonical_name: str,
    entity_type: str,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Insert or retrieve entity ID by canonical name."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    init_db(db_path)
    with get_db(db_path) as conn:
        cur = conn.execute(
            "SELECT id FROM entities WHERE canonical_name = ?", (canonical_name,)
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur = conn.execute(
            "INSERT INTO entities (canonical_name, entity_type, created_at) VALUES (?, ?, ?)",
            (canonical_name, entity_type, now_iso),
        )
        conn.commit()
        return cur.lastrowid


def insert_relation(
    source_entity_id: int,
    target_entity_id: int,
    relation_type: str,
    source_id: int,
    confidence: float = 1.0,
    occurred_at: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[int]:
    """Insert relation triple with source provenance."""
    init_db(db_path)
    with get_db(db_path) as conn:
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO relations 
                (source_entity_id, target_entity_id, relation_type, confidence, source_id, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_entity_id, target_entity_id, relation_type, confidence, source_id, occurred_at),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            return None


def get_all_entities_and_relations(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Retrieve full graph dataset with node/edge details and source provenance."""
    init_db(db_path)
    with get_db(db_path) as conn:
        nodes_cur = conn.execute("SELECT id, canonical_name, entity_type, created_at FROM entities")
        nodes = [dict(row) for row in nodes_cur.fetchall()]

        edges_cur = conn.execute("""
            SELECT 
                r.id, 
                r.source_entity_id, 
                r.target_entity_id, 
                e1.canonical_name as source_name,
                e2.canonical_name as target_name,
                r.relation_type, 
                r.confidence, 
                r.source_id,
                s.title as source_title,
                s.url as source_url,
                s.published as source_date
            FROM relations r
            JOIN entities e1 ON r.source_entity_id = e1.id
            JOIN entities e2 ON r.target_entity_id = e2.id
            JOIN sources s ON r.source_id = s.id
        """)
        edges = [dict(row) for row in edges_cur.fetchall()]

        return {"nodes": nodes, "edges": edges}
