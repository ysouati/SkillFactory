"""5-config retrieval ablation on MultiHop-RAG, to justify the retrieval design.

Configs (each adds to the previous):
  1. Dense only          - text-embedding-3-large semantic vector
  2. Dense + sparse       - normalized dense+bm25 score fusion
  3. Hybrid RRF           - reciprocal-rank fusion of the two branches
  4. + Metadata-aware     - structured analog for this corpus: boost candidate
                            docs whose metadata (source / category / title
                            entities / publish date) is consistent with the query
  5. + LLM reranking      - gpt-4.1-mini listwise reorder of the top candidates

Relevance = doc-level: a query's evidence_list titles (avg 2.7) are the gold docs;
each corpus doc has a unique title. Metrics @10: MRR, MAP, Recall, Hits.
null_query rows (no evidence) are excluded. Uses its OWN Qdrant store, so the KB
service can stay running.

Run:  cd benchmarks/multihop_rag && python ablation.py
Env:  AZURE_API_KEY (required), ABLATION_N (queries to sample, default 300)
"""
import json
import os
import random
import re
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "kb"))

from openai import OpenAI
from qdrant_client import QdrantClient

from embeddings import embed_batch
from settings import AZURE_BASE_URL, RERANK_MODEL, get_api_key
from sparse import sparse_query

QDRANT_PATH = HERE / "qdrant"
COLLECTION = "multihop"
DENSE, SPARSE = "dense", "bm25"

K_CHUNKS = 60      # chunk hits pulled per branch before collapsing to docs
CAND = 10          # docs handed to metadata boost / LLM reranker
DEPTH = 10         # metric cutoff (@10)
BOOST_W = 0.5      # weight of the metadata signal relative to normalized RRF
N = int(os.getenv("ABLATION_N", "300"))
SEED = 13

CONFIGS = ["dense", "dense+sparse", "hybrid_rrf", "+metadata", "+rerank"]

_ENT = re.compile(r"\b([A-Z][a-zA-Z0-9&.'-]+(?:\s+[A-Z][a-zA-Z0-9&.'-]+)*)\b")
_YEAR = re.compile(r"\b(?:19|20)\d\d\b")
_MONTHS = [
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
]


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------
def load_meta() -> dict:
    corpus = json.loads((HERE / "data" / "corpus.json").read_text(encoding="utf-8"))
    return {d["title"]: d for d in corpus}


def load_queries(n: int) -> list[dict]:
    q = json.loads((HERE / "data" / "MultiHopRAG.json").read_text(encoding="utf-8"))
    q = [x for x in q if x.get("question_type") != "null_query" and x.get("evidence_list")]
    # stratified sample by question_type for a representative slice
    by_type = defaultdict(list)
    for x in q:
        by_type[x["question_type"]].append(x)
    rng = random.Random(SEED)
    out = []
    if n >= len(q):
        out = q
    else:
        for t, rows in by_type.items():
            rng.shuffle(rows)
            take = max(1, round(n * len(rows) / len(q)))
            out.extend(rows[:take])
        rng.shuffle(out)
        out = out[:n]
    for x in out:
        x["_relevant"] = {e["title"] for e in x["evidence_list"]}
    return out


# ---------------------------------------------------------------------------
# fusion primitives
# ---------------------------------------------------------------------------
def collapse(points) -> tuple[list, dict]:
    """Chunk hits -> ranked unique doc_ids (best chunk per doc), with best score."""
    order, score = [], {}
    for pt in points:
        did = pt.payload["doc_id"]
        if did not in score:
            score[did] = pt.score
            order.append(did)
    return order, score


def rrf(rank_lists, k: int = 60) -> tuple[list, dict]:
    s = defaultdict(float)
    for ranks in rank_lists:
        for i, c in enumerate(ranks):
            s[c] += 1.0 / (k + i + 1)
    return sorted(s, key=lambda c: s[c], reverse=True), dict(s)


def entities(text: str) -> set:
    return {m.group(1).lower() for m in _ENT.finditer(text or "") if len(m.group(1)) > 2}


def metadata_boost(query: str, cand: list, meta: dict) -> dict:
    """Structured/metadata analog: reward candidate docs whose metadata is
    consistent with the query - named source, category, title-entity overlap,
    and shared year/month (temporal). Deterministic, no LLM."""
    ql = query.lower()
    q_ents = entities(query)
    q_years = set(_YEAR.findall(query))
    q_months = {m for m in _MONTHS if m in ql}
    boost = {}
    for did in cand:
        d = meta.get(did, {})
        b = 0.0
        src = (d.get("source") or "").lower()
        cat = (d.get("category") or "").lower()
        if src and src in ql:
            b += 1.0
        if cat and cat in ql:
            b += 0.4
        t_ents = entities(did)
        if q_ents and t_ents:
            b += 1.2 * len(q_ents & t_ents) / len(t_ents)
        pub = (d.get("published_at") or "").lower()   # ISO: 2023-11-27T...
        if q_years and any(y in pub for y in q_years):
            b += 0.5
        if q_months:
            mon = ""
            parts = pub.split("-")
            if len(parts) >= 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12:
                mon = _MONTHS[int(parts[1]) - 1]
            if mon and mon in q_months:
                b += 0.5
        boost[did] = b
    return boost


@lru_cache(maxsize=1)
def _llm() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL)


def llm_rerank(query: str, docs: list, meta: dict) -> list:
    lines = []
    for i, did in enumerate(docs, 1):
        d = meta.get(did, {})
        snip = (d.get("body") or "")[:200].replace("\n", " ")
        lines.append(f"{i}. {did} [{d.get('source')}] :: {snip}")
    prompt = (
        "Given a question and candidate news articles, rank the articles from most "
        "to least useful for answering it. Return ONLY the article numbers in ranked "
        "order, comma-separated (e.g. 3,1,2).\n\n"
        f"Question: {query}\n\nArticles:\n" + "\n".join(lines)
    )
    try:
        r = _llm().chat.completions.create(
            model=RERANK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=100,
        )
        nums = re.findall(r"\d+", r.choices[0].message.content or "")
        seen, out = set(), []
        for tok in nums:
            j = int(tok) - 1
            if 0 <= j < len(docs) and docs[j] not in seen:
                seen.add(docs[j])
                out.append(docs[j])
        out += [d for d in docs if d not in seen]  # append any the model dropped
        return out
    except Exception:
        return list(docs)


# ---------------------------------------------------------------------------
# metrics @DEPTH (doc-level)
# ---------------------------------------------------------------------------
def score(ranked: list, relevant: set, depth: int = DEPTH) -> tuple:
    topk = ranked[:depth]
    mrr = 0.0
    for i, did in enumerate(topk):
        if did in relevant:
            mrr = 1.0 / (i + 1)
            break
    hits, ap = 0, 0.0
    for i, did in enumerate(topk):
        if did in relevant:
            hits += 1
            ap += hits / (i + 1)
    ap = ap / min(len(relevant), depth) if relevant else 0.0
    found = set(topk) & relevant
    recall = len(found) / len(relevant) if relevant else 0.0
    hit = 1.0 if found else 0.0
    return mrr, ap, recall, hit


def main() -> None:
    meta = load_meta()
    queries = load_queries(N)
    print(f"MultiHop-RAG ablation: {len(queries)} queries, corpus {len(meta)} docs.", flush=True)

    client = QdrantClient(path=str(QDRANT_PATH))
    qvecs = embed_batch([x["query"] for x in queries])

    agg = {c: {"mrr": 0.0, "map": 0.0, "recall": 0.0, "hits": 0.0} for c in CONFIGS}

    for i, (x, qv) in enumerate(zip(queries, qvecs), 1):
        rel = x["_relevant"]
        dpts = client.query_points(COLLECTION, query=qv, using=DENSE, limit=K_CHUNKS).points
        spts = client.query_points(
            COLLECTION, query=sparse_query(x["query"]), using=SPARSE, limit=K_CHUNKS
        ).points
        d_rank, d_score = collapse(dpts)
        s_rank, s_score = collapse(spts)

        # C1 dense
        c1 = d_rank
        # C2 dense+sparse normalized fusion
        dm = max(d_score.values()) if d_score else 1.0
        sm = max(s_score.values()) if s_score else 1.0
        lin = defaultdict(float)
        for c, v in d_score.items():
            lin[c] += v / dm
        for c, v in s_score.items():
            lin[c] += v / sm
        c2 = sorted(lin, key=lambda c: lin[c], reverse=True)
        # C3 hybrid RRF
        c3, rrf_scores = rrf([d_rank, s_rank])
        # C4 + metadata boost (over the RRF candidate head)
        head = c3[: max(CAND, 25)]
        rmax = max(rrf_scores.values()) if rrf_scores else 1.0
        boost = metadata_boost(x["query"], head, meta)
        fused = {c: rrf_scores[c] / rmax + BOOST_W * boost.get(c, 0.0) for c in head}
        c4 = sorted(fused, key=lambda c: fused[c], reverse=True) + c3[max(CAND, 25):]
        # C5 + LLM rerank of the top CAND
        c5 = llm_rerank(x["query"], c4[:CAND], meta) + c4[CAND:]

        for name, ranked in zip(CONFIGS, [c1, c2, c3, c4, c5]):
            mrr, ap, rec, hit = score(ranked, rel)
            agg[name]["mrr"] += mrr
            agg[name]["map"] += ap
            agg[name]["recall"] += rec
            agg[name]["hits"] += hit

        if i % 25 == 0 or i == len(queries):
            print(
                f"  {i}/{len(queries)}  MRR@10: "
                + " ".join(f"{c}={agg[c]['mrr'] / i:.3f}" for c in CONFIGS),
                flush=True,
            )

    n = len(queries)
    print(f"\n{'config':<15} {'MRR@10':>8} {'MAP@10':>8} {'Recall@10':>10} {'Hits@10':>8}")
    print("-" * 53)
    summary = {}
    for c in CONFIGS:
        row = {k: round(v / n * (100 if k in ("recall", "hits") else 1), 3 if k in ("mrr", "map") else 1)
               for k, v in agg[c].items()}
        summary[c] = row
        print(f"{c:<15} {row['mrr']:>8.3f} {row['map']:>8.3f} {row['recall']:>9.1f}% {row['hits']:>7.1f}%")

    out = HERE / "ablation_results.json"
    out.write_text(json.dumps({"n": n, "depth": DEPTH, "configs": summary}, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out}")
    client.close()


if __name__ == "__main__":
    main()
