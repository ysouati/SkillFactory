from dataclasses import dataclass
from typing import Optional

from qdrant_client import models

from embeddings import embed
from settings import (
    DENSE_VECTOR,
    FINAL_K,
    HYBRID_PREFETCH,
    PROSE_COLLECTION,
    RERANK_TOP_N,
    SPARSE_VECTOR,
)
from sparse import sparse_query


@dataclass
class Hit:
    text: str
    citation: str
    source_id: str
    source_url: str
    doc_type: str
    score: float


def _to_hit(point) -> Hit:
    p = point.payload
    return Hit(
        text=p["text"],
        citation=p["citation"],
        source_id=p["source_id"],
        source_url=p["source_url"],
        doc_type=p["doc_type"],
        score=point.score,
    )


def _doc_type_filter(doc_type: Optional[str]) -> Optional[models.Filter]:
    if not doc_type:
        return None
    return models.Filter(
        must=[models.FieldCondition(key="doc_type", match=models.MatchValue(value=doc_type))]
    )


def dense_search(client, query: str, k: int = FINAL_K, doc_type: Optional[str] = None) -> list[Hit]:
    hits = client.query_points(
        collection_name=PROSE_COLLECTION,
        query=embed(query),
        using=DENSE_VECTOR,
        query_filter=_doc_type_filter(doc_type),
        limit=k,
        with_payload=True,
    ).points
    return [_to_hit(h) for h in hits]


def hybrid_search(client, query: str, k: int = FINAL_K, doc_type: Optional[str] = None) -> list[Hit]:
    """Dense + BM25 branches fused with Reciprocal Rank Fusion."""
    flt = _doc_type_filter(doc_type)
    hits = client.query_points(
        collection_name=PROSE_COLLECTION,
        prefetch=[
            models.Prefetch(query=embed(query), using=DENSE_VECTOR, limit=HYBRID_PREFETCH, filter=flt),
            models.Prefetch(query=sparse_query(query), using=SPARSE_VECTOR, limit=HYBRID_PREFETCH, filter=flt),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=k,
        with_payload=True,
    ).points
    return [_to_hit(h) for h in hits]


def search(client, query: str, k: int = FINAL_K, doc_type: Optional[str] = None) -> list[Hit]:
    """The full retrieval path: hybrid recall -> LLM rerank -> top k.

    This is the function the factory's search_docs tool will call.
    """
    from rerank import rerank

    candidates = hybrid_search(client, query, k=RERANK_TOP_N, doc_type=doc_type)
    return rerank(query, candidates, top_k=k)


def backfill_sparse(client, batch: int = 256) -> int:
    """Add BM25 sparse vectors to points that only have dense vectors, WITHOUT
    re-embedding (reads text from payload). Use this to add hybrid to an already
    dense-embedded large corpus cheaply."""
    from sparse import sparse_docs

    offset = None
    total = 0
    while True:
        points, offset = client.scroll(
            PROSE_COLLECTION, limit=batch, offset=offset, with_payload=True, with_vectors=False
        )
        if not points:
            break
        texts = [p.payload["text"] for p in points]
        svecs = sparse_docs(texts)
        client.update_vectors(
            collection_name=PROSE_COLLECTION,
            points=[
                models.PointVectors(id=p.id, vector={SPARSE_VECTOR: sv})
                for p, sv in zip(points, svecs)
            ],
        )
        total += len(points)
        if offset is None:
            break
    return total
