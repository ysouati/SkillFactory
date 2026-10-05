import sqlite3
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, SparseVectorParams, VectorParams

from settings import (
    DENSE_VECTOR,
    EMBED_DIM,
    FACT_DB_PATH,
    KB_ROOT,
    PROSE_COLLECTION,
    QDRANT_PATH,
    SPARSE_VECTOR,
)


# ---------------------------------------------------------------------------
# Prose store: Qdrant with named dense + sparse (BM25) vectors for hybrid search
# ---------------------------------------------------------------------------
def get_vector_client() -> QdrantClient:
    KB_ROOT.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_PATH))


def ensure_prose_collection(client: QdrantClient) -> None:
    if client.collection_exists(PROSE_COLLECTION):
        return
    client.create_collection(
        collection_name=PROSE_COLLECTION,
        vectors_config={
            DENSE_VECTOR: VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            SPARSE_VECTOR: SparseVectorParams(),
        },
    )


# ---------------------------------------------------------------------------
# Fact store: SQLite for exact-lookup structured data + the ingest manifest
# ---------------------------------------------------------------------------
def get_fact_db() -> sqlite3.Connection:
    KB_ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FACT_DB_PATH))
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Generic structured store: any source (ATT&CK, CWE, CVE, ...) maps into the
    same entities / attributes / relations shape, queried exactly. Plus the ingest
    manifest for incremental prose ingestion."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingest_manifest (
            path          TEXT PRIMARY KEY,
            content_hash  TEXT NOT NULL,
            doc_type      TEXT,
            format        TEXT,
            n_chunks      INTEGER,
            ingested_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS entities (
            entity_id     TEXT PRIMARY KEY,   -- e.g. "T1055", "TA0004", "CWE-121"
            entity_type   TEXT NOT NULL,      -- e.g. "attack-technique", "attack-tactic"
            name          TEXT,
            summary       TEXT,
            source_id     TEXT
        );

        CREATE TABLE IF NOT EXISTS attributes (
            entity_id     TEXT NOT NULL,
            key           TEXT NOT NULL,
            value         TEXT,
            PRIMARY KEY (entity_id, key, value)
        );

        CREATE TABLE IF NOT EXISTS relations (
            src_id        TEXT NOT NULL,
            rel_type      TEXT NOT NULL,      -- e.g. "uses", "mitigates", "subtechnique-of"
            dst_id        TEXT NOT NULL,
            PRIMARY KEY (src_id, rel_type, dst_id)
        );

        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_attributes_kv ON attributes(key, value);
        CREATE INDEX IF NOT EXISTS idx_relations_src ON relations(src_id, rel_type);
        CREATE INDEX IF NOT EXISTS idx_relations_dst ON relations(dst_id, rel_type);
        """
    )
    conn.commit()


if __name__ == "__main__":
    vc = get_vector_client()
    ensure_prose_collection(vc)
    info = vc.get_collection(PROSE_COLLECTION)
    print(f"Prose collection '{PROSE_COLLECTION}' ready.")
    print(f"  points: {vc.count(PROSE_COLLECTION).count}")
    print(f"  dense vectors: {list(info.config.params.vectors.keys())}")
    print(f"  sparse vectors: {list((info.config.params.sparse_vectors or {}).keys())}")
    vc.close()

    db = get_fact_db()
    tables = [r["name"] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    print(f"\nFact DB ready at {FACT_DB_PATH.name}")
    print(f"  tables: {tables}")
    db.close()
