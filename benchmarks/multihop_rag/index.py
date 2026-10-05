"""Index the MultiHop-RAG corpus into an ISOLATED local Qdrant store.

Separate from the KB's kb_data/qdrant, so the running KB service is untouched
(no shared file lock). Builds named dense (text-embedding-3-large) + bm25 sparse
vectors over char-chunked article bodies. Payload carries doc metadata so the
ablation's metadata-aware config can use it.

Run:  cd benchmarks/multihop_rag && python index.py
Needs AZURE_API_KEY in env (for the dense embeddings).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "kb"))  # reuse kb embedding/sparse helpers

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

from embeddings import embed_batch
from sparse import sparse_docs

QDRANT_PATH = HERE / "qdrant"
COLLECTION = "multihop"
DENSE, SPARSE = "dense", "bm25"
DIM = 3072
CHUNK_CHARS = 1500
OVERLAP = 200


def chunk_text(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out, i, step = [], 0, size - overlap
    while i < len(text):
        out.append(text[i : i + size])
        i += step
    return out


def main() -> None:
    corpus = json.loads((HERE / "data" / "corpus.json").read_text(encoding="utf-8"))
    chunks = []
    for d in corpus:
        title = d["title"]
        for ci, ch in enumerate(chunk_text(d.get("body", ""))):
            chunks.append(
                {
                    "doc_id": title,
                    "source": d.get("source"),
                    "category": d.get("category"),
                    "published_at": d.get("published_at"),
                    "chunk": ci,
                    "text": ch,
                }
            )
    print(f"docs={len(corpus)}  chunks={len(chunks)}", flush=True)

    client = QdrantClient(path=str(QDRANT_PATH))
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION,
        vectors_config={DENSE: VectorParams(size=DIM, distance=Distance.COSINE)},
        sparse_vectors_config={SPARSE: SparseVectorParams()},
    )

    texts = [c["text"] for c in chunks]
    print("embedding dense (text-embedding-3-large)...", flush=True)
    dense = embed_batch(texts, batch_size=64)
    print("embedding sparse (bm25)...", flush=True)
    sp = sparse_docs(texts)

    points = [
        PointStruct(id=i, vector={DENSE: dv, SPARSE: sv}, payload=c)
        for i, (c, dv, sv) in enumerate(zip(chunks, dense, sp))
    ]
    B = 256
    for i in range(0, len(points), B):
        client.upsert(COLLECTION, points[i : i + B])
        print(f"  upserted {min(i + B, len(points))}/{len(points)}", flush=True)

    print(f"done. collection '{COLLECTION}' count={client.count(COLLECTION).count}")
    client.close()


if __name__ == "__main__":
    main()
