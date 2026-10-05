import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

# Allow importing the shared kb/ runtime modules (settings, stores, embeddings, sparse)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client.models import PointStruct

from chunking import chunk_text
from embeddings import embed_batch
from loaders import SourceUnit
from settings import (
    CHUNK_CHARS,
    CHUNK_OVERLAP,
    DENSE_VECTOR,
    EMBED_BATCH,
    KB_ROOT,
    PROSE_COLLECTION,
    SPARSE_VECTOR,
)
from sparse import sparse_docs
from stores import ensure_prose_collection, get_fact_db, get_vector_client

CORPUS_DIR = KB_ROOT / "corpus"


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    subprocess.run(["curl", "-sL", url, "-o", str(dest)], check=True, timeout=300)
    return dest


def _file_hash(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _point_id(source_id: str, unit_key: str, idx: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"{source_id}::{unit_key}::{idx}"))


def _already_ingested(db, path: Path, content_hash: str) -> bool:
    row = db.execute(
        "SELECT content_hash FROM ingest_manifest WHERE path = ?", (str(path),)
    ).fetchone()
    return row is not None and row["content_hash"] == content_hash


def ingest_units(
    units: list[SourceUnit],
    source_file: Path,
    client,
    db,
    force: bool = False,
) -> int:
    """Chunk -> embed (dense) -> upsert with citation payload. Idempotent per file hash."""
    if not units:
        return 0
    content_hash = _file_hash(source_file)
    if not force and _already_ingested(db, source_file, content_hash):
        print(f"  skip (unchanged): {source_file.name}")
        return 0

    texts: list[str] = []
    metas: list[tuple[SourceUnit, int, str]] = []
    for u in units:
        for idx, ch in enumerate(chunk_text(u.text, CHUNK_CHARS, CHUNK_OVERLAP)):
            texts.append(ch)
            metas.append((u, idx, ch))

    if not texts:
        return 0

    print(f"  embedding {len(texts)} chunks from {len(units)} units...")
    vecs = embed_batch(texts, batch_size=EMBED_BATCH)
    svecs = sparse_docs(texts)

    points = []
    for (u, idx, ch), vec, svec in zip(metas, vecs, svecs):
        cite = u.citation if idx == 0 else f"{u.citation} (cont. {idx})"
        payload = {
            "text": ch,
            "source_id": u.source_id,
            "source_title": u.source_title,
            "source_url": u.source_url,
            "doc_type": u.doc_type,
            "format": u.format,
            "unit_key": u.unit_key,
            "chunk_index": idx,
            "citation": cite,
            **u.extra,
        }
        points.append(
            PointStruct(
                id=_point_id(u.source_id, u.unit_key, idx),
                vector={DENSE_VECTOR: vec, SPARSE_VECTOR: svec},
                payload=payload,
            )
        )

    for i in range(0, len(points), 256):
        client.upsert(collection_name=PROSE_COLLECTION, points=points[i : i + 256])

    db.execute(
        "INSERT OR REPLACE INTO ingest_manifest "
        "(path, content_hash, doc_type, format, n_chunks, ingested_at) VALUES (?,?,?,?,?,?)",
        (
            str(source_file),
            content_hash,
            units[0].doc_type,
            units[0].format,
            len(points),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()
    return len(points)


def ingest_starter_corpus(attack_limit: int | None = 200, force: bool = False) -> None:
    from loaders import load_pdf, load_stix_attack

    client = get_vector_client()
    ensure_prose_collection(client)
    db = get_fact_db()

    # --- Source 1: NIST SP 800-171 Rev. 2 (PDF) ---
    print("NIST SP 800-171 Rev. 2:")
    nist_pdf = download(
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r2.pdf",
        CORPUS_DIR / "nist-sp-800-171r2.pdf",
    )
    nist_units = load_pdf(
        nist_pdf,
        source_id="nist-sp-800-171r2",
        source_title="NIST SP 800-171 Rev. 2",
        source_url="https://csrc.nist.gov/pubs/sp/800/171/r2/upd1/final",
    )
    n1 = ingest_units(nist_units, nist_pdf, client, db, force=force)
    print(f"  -> {n1} chunks ingested")

    # --- Source 2: MITRE ATT&CK Enterprise (STIX JSON) ---
    print("\nMITRE ATT&CK Enterprise:")
    attack_json = download(
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
        CORPUS_DIR / "enterprise-attack.json",
    )
    attack_units = load_stix_attack(
        attack_json,
        source_id="mitre-attack-enterprise",
        source_title="MITRE ATT&CK Enterprise",
        limit=attack_limit,
    )
    n2 = ingest_units(attack_units, attack_json, client, db, force=force)
    print(f"  -> {n2} chunks ingested (limit={attack_limit})")

    total = client.count(PROSE_COLLECTION).count
    print(f"\nProse collection now holds {total} chunks total.")
    client.close()
    db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--attack-limit", type=int, default=200,
                        help="Max ATT&CK techniques to ingest (0 = all)")
    parser.add_argument("--force", action="store_true",
                        help="Re-ingest even if the source file is unchanged")
    args = parser.parse_args()
    ingest_starter_corpus(attack_limit=args.attack_limit or None, force=args.force)
