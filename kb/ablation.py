"""Retrieval ablation over the CWE catalog on the CTI-RCM CVE->CWE task.

Query = CVE description. Metric = whether the ground-truth CWE is retrieved
(Recall@1 = top result matches, Recall@5 = in top 5). Five nested configs:
  1. Dense only              (semantic vector)
  2. Dense + sparse          (normalized score fusion)
  3. Hybrid RRF              (reciprocal-rank fusion)
  4. + structured knowledge  (CWE hierarchy: boost common ancestors of candidates)
  5. + LLM reranking         (gpt-4.1-mini reorders the candidates)

Opens Qdrant directly, so the KB service must be STOPPED while this runs.
"""
import json
import os
import re
import subprocess
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from openai import OpenAI
from qdrant_client import models

from embeddings import embed_batch
from settings import (
    AZURE_BASE_URL,
    DENSE_VECTOR,
    PROSE_COLLECTION,
    RERANK_MODEL,
    SPARSE_VECTOR,
    get_api_key,
)
from sparse import sparse_query
from stores import get_fact_db, get_vector_client

N = int(os.getenv("ABLATION_N", "150"))
K = 20            # retrieval depth per branch
CAND = 8          # candidates handed to structured/rerank
TSV_URL = "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-rcm.tsv"
_CWE = re.compile(r"CWE-\d+", re.IGNORECASE)
_CWE_FILTER = models.Filter(
    must=[models.FieldCondition(key="doc_type", match=models.MatchValue(value="cwe"))]
)


def norm(x):
    m = _CWE.findall(str(x))
    return m[-1].upper() if m else str(x).upper()


def load_rows(n):
    tsv = Path(__file__).parent.parent / "kb_data" / "corpus" / "cti-rcm.tsv"
    tsv.parent.mkdir(parents=True, exist_ok=True)
    if not tsv.exists():
        subprocess.run(["curl", "-sL", TSV_URL, "-o", str(tsv)], check=True, timeout=120)
    lines = tsv.read_text(encoding="utf-8").splitlines()
    h = lines[0].split("\t")
    di, gi = h.index("Description"), h.index("GT")
    rows = []
    for line in lines[1 : n + 1]:
        p = line.split("\t")
        if len(p) > max(di, gi):
            rows.append({"desc": p[di], "gt": norm(p[gi])})
    return rows


def collapse(points):
    """Chunk hits -> ranked unique CWE ids (best chunk per CWE), with best score."""
    order, score = [], {}
    for pt in points:
        cid = pt.payload["unit_key"]
        if cid not in score:
            score[cid] = pt.score
            order.append(cid)
    return order, score


def rrf(rank_lists, k=60):
    s = defaultdict(float)
    for ranks in rank_lists:
        for i, c in enumerate(ranks):
            s[c] += 1.0 / (k + i + 1)
    return sorted(s, key=lambda c: s[c], reverse=True), dict(s)


@lru_cache(maxsize=4000)
def parents_of(cid):
    db = _factdb()
    rows = db.execute(
        "SELECT dst_id FROM relations WHERE src_id = ? AND rel_type = 'child-of'", (cid,)
    ).fetchall()
    return tuple(r["dst_id"] for r in rows)


@lru_cache(maxsize=4000)
def cwe_name(cid):
    db = _factdb()
    r = db.execute("SELECT name, summary FROM entities WHERE entity_id = ?", (cid,)).fetchone()
    return (r["name"], r["summary"]) if r else ("", "")


_FACTDB = None
def _factdb():
    global _FACTDB
    if _FACTDB is None:
        _FACTDB = get_fact_db()
    return _FACTDB


@lru_cache(maxsize=1)
def _llm():
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL)


def structured_rerank(rrf_scores, top):
    """Boost candidates' hierarchy ancestors: a CWE that is the parent of retrieved
    candidates accumulates their score (consensus toward the general/Base weakness)."""
    s = dict(rrf_scores)
    for c in top:
        for par in parents_of(c):
            s[par] = s.get(par, 0.0) + 0.6 * rrf_scores.get(c, 0.0)
    return sorted(s, key=lambda c: s[c], reverse=True)


def llm_rerank(desc, candidates):
    lines = []
    for c in candidates:
        name, summ = cwe_name(c)
        lines.append(f"{c}: {name} - {summ[:160]}")
    prompt = (
        "Given a CVE description and candidate CWE weaknesses, rank the candidates from "
        "most to least appropriate for classifying the described weakness. Return ONLY the "
        "CWE ids in ranked order, comma-separated.\n\n"
        f"CVE: {desc}\n\nCandidates:\n" + "\n".join(lines)
    )
    try:
        r = _llm().chat.completions.create(
            model=RERANK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=200,
        )
        ordered = _CWE.findall(r.choices[0].message.content or "")
        ordered = [c.upper() for c in ordered]
        # keep only known candidates, then append any missed
        seen = set()
        out = [c for c in ordered if c in candidates and not (c in seen or seen.add(c))]
        out += [c for c in candidates if c not in seen]
        return out
    except Exception:
        return list(candidates)


def main():
    rows = load_rows(N)
    print(f"Ablation on {len(rows)} CVEs (CWE retrieval). Embedding queries...", flush=True)
    vc = get_vector_client()
    qvecs = embed_batch([r["desc"] for r in rows])

    configs = ["dense", "dense+sparse", "hybrid_rrf", "+structured", "+rerank"]
    hit1 = {c: 0 for c in configs}
    hit5 = {c: 0 for c in configs}

    for i, (row, qv) in enumerate(zip(rows, qvecs), 1):
        gt = row["gt"]
        dpts = vc.query_points(PROSE_COLLECTION, query=qv, using=DENSE_VECTOR,
                               query_filter=_CWE_FILTER, limit=K).points
        spts = vc.query_points(PROSE_COLLECTION, query=sparse_query(row["desc"]), using=SPARSE_VECTOR,
                               query_filter=_CWE_FILTER, limit=K).points
        d_rank, d_score = collapse(dpts)
        s_rank, s_score = collapse(spts)

        # C1 dense
        c1 = d_rank
        # C2 dense+sparse: normalized score sum
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
        # C4 + structured
        c4 = structured_rerank(rrf_scores, c3[:CAND])
        # C5 + rerank
        c5 = llm_rerank(row["desc"], c4[:CAND])

        for name, ranked in zip(configs, [c1, c2, c3, c4, c5]):
            if ranked and ranked[0] == gt:
                hit1[name] += 1
            if gt in ranked[:5]:
                hit5[name] += 1

        if i % 25 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}  R@1: " +
                  " ".join(f"{c}={hit1[c]/i*100:.0f}" for c in configs), flush=True)

    n = len(rows)
    print(f"\n{'config':<16} {'Recall@1':>10} {'Recall@5':>10}")
    print("-" * 38)
    summary = {}
    for c in configs:
        r1, r5 = hit1[c] / n * 100, hit5[c] / n * 100
        summary[c] = {"recall@1": round(r1, 1), "recall@5": round(r5, 1)}
        print(f"{c:<16} {r1:>9.1f}% {r5:>9.1f}%")

    out = Path(__file__).parent.parent / "kb_data" / "ablation_results.json"
    out.write_text(json.dumps({"n": n, "configs": summary}, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out}")
    vc.close()


if __name__ == "__main__":
    main()
