from functools import lru_cache

from openai import OpenAI
from pydantic import BaseModel, Field

from settings import AZURE_BASE_URL, RERANK_MODEL, get_api_key


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL)


class RankedItem(BaseModel):
    index: int = Field(description="The candidate number as shown in the list.")
    relevance: float = Field(ge=0.0, le=1.0, description="0.0 (irrelevant) to 1.0 (directly answers the query).")


class RerankResult(BaseModel):
    ranking: list[RankedItem] = Field(description="Candidates ordered best-first. Omit clearly irrelevant ones.")


SYSTEM = """You are a precise retrieval reranker for a cybersecurity knowledge base.

Given a query and a numbered list of candidate passages, rank the candidates by
how well each one actually answers the query. Judge on substance, not keyword
overlap: a passage that merely mentions the query terms but doesn't address the
question is NOT relevant. Assign each candidate a relevance score from 0 to 1 and
return them ordered best-first. Drop candidates that are clearly irrelevant."""


def _snippet(text: str, limit: int = 600) -> str:
    text = " ".join(text.split())
    return text[:limit]


def rerank(query: str, hits: list, top_k: int, snippet_chars: int = 600) -> list:
    """Listwise LLM rerank. Falls back to the input order on any failure."""
    if len(hits) <= 1:
        return hits[:top_k]

    listing = "\n".join(
        f"[{i}] ({h.citation}) {_snippet(h.text, snippet_chars)}"
        for i, h in enumerate(hits)
    )
    user = f"Query: {query}\n\nCandidates:\n{listing}"

    try:
        resp = _client().beta.chat.completions.parse(
            model=RERANK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            response_format=RerankResult,
            temperature=0,
        )
        ranking = resp.choices[0].message.parsed.ranking
    except Exception:
        return hits[:top_k]

    ordered: list = []
    seen: set[int] = set()
    for item in ranking:
        if 0 <= item.index < len(hits) and item.index not in seen:
            h = hits[item.index]
            h.score = item.relevance
            ordered.append(h)
            seen.add(item.index)

    # Backfill anything the model dropped, preserving original hybrid order.
    for i, h in enumerate(hits):
        if i not in seen:
            ordered.append(h)

    return ordered[:top_k]
