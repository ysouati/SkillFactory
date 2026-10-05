from functools import lru_cache

from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector


@lru_cache(maxsize=1)
def _model() -> SparseTextEmbedding:
    # Statistical BM25 (tokenizer + IDF), computed client-side. No neural model,
    # no Azure dependency. Document and query sides are embedded differently.
    return SparseTextEmbedding("Qdrant/bm25")


def _to_sparse(emb) -> SparseVector:
    return SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())


def sparse_docs(texts: list[str]) -> list[SparseVector]:
    return [_to_sparse(e) for e in _model().embed(texts)]


def sparse_query(text: str) -> SparseVector:
    return _to_sparse(next(iter(_model().query_embed([text]))))
