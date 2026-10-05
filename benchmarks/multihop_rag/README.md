# MultiHop-RAG Retrieval Ablation

Benchmarks the skill-factory **retrieval component** to justify its design, by measuring
how much each layer of the pipeline (dense → sparse → fusion → structure → rerank)
contributes to retrieval quality on an external, recognized RAG benchmark.

This is a **self-contained** study: it has its own Qdrant store and its own copy of the
data, so it does **not** touch the KB's `kb_data/qdrant` (the KB service can stay running).

---

## 1. The benchmark: MultiHop-RAG

**MultiHop-RAG** (Tang & Yang, 2024) is a QA dataset built to evaluate *retrieval and
reasoning across multiple documents* in RAG pipelines — the answer to each query is spread
over 2–4 news articles, so a retriever must surface several relevant documents, not just one.

- Paper: *MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries* (2024)
- Code: <https://github.com/yixuantt/MultiHop-RAG> (ships evaluation code only)
- Data: <https://huggingface.co/datasets/yixuantt/MultiHopRAG> (`corpus.json`, `MultiHopRAG.json`)

### Why this benchmark (fit to our project)

- We wanted an **external, recognized** retrieval benchmark with real relevance labels (qrels).
  No standard *cybersecurity* passage-IR benchmark with qrels exists (BEIR is the standard suite
  but has no security corpus; CyberQ/AISecKG is domain-matched but not cleanly downloadable with
  retrieval labels), so MultiHop-RAG was the best available choice.
- It tests **passage retrieval for QA** — exactly what our *prose store* does day-to-day — which is
  more representative of the component than our earlier CWE **entity**-retrieval ablation (`kb/ablation.py`).
- It reports the same evaluation axes as our design (embedding models **and** rerankers), and its
  multi-hop nature stresses **recall** (must gather several evidence docs), which our metadata +
  rerank layers target.

---

## 2. The corpus

`data/corpus.json` — **609 news articles** (Sept–Dec 2023), each with:

| field | example | notes |
|---|---|---|
| `title` | "The FTX trial is bigger than Sam Bankman-Fried" | **unique** across all 609 docs → used as the doc id / relevance key |
| `author` | "Elizabeth Lopatto" | often `None` |
| `source` | "The Verge" | **49 distinct sources** (TechCrunch, The Verge, Hacker News, BBC, …) |
| `published_at` | "2023-09-28T12:00:00+00:00" | ISO timestamp (used by the temporal metadata boost) |
| `category` | "technology" | technology / business / sports / entertainment / science |
| `url` | … | source link |
| `body` | ~5.8k chars avg | article text; chunked for indexing |

**Indexing** (`index.py`): bodies are char-chunked (`1500` chars, `200` overlap) → **5,144 chunks**,
each embedded with **dense** (`text-embedding-3-large`, 3072-d, cosine) **+ sparse** (`Qdrant/bm25`)
named vectors into the isolated `multihop` Qdrant collection. Chunk payload keeps `doc_id` (=title),
`source`, `category`, `published_at` so the metadata-aware config can use them.

---

## 3. The queries and their types

`data/MultiHopRAG.json` — **2,556 queries**. Each has `query`, `answer`, `question_type`, and
`evidence_list` (the gold supporting documents).

| question_type | count | what it asks |
|---|---:|---|
| `comparison_query` | 856 | Compare a property across entities/articles ("do both X and Y report a revenue increase?") |
| `inference_query` | 816 | Bridge across docs via a shared entity ("who is the person reported by both The Verge and TechCrunch…?") |
| `temporal_query` | 583 | Reason about the order/timing of events across dated articles |
| `null_query` | 301 | **Distractor** — the answer is *not* in the corpus; gold answer is "Insufficient information" and `evidence_list` is empty |
| **answerable total** | **2,255** | (all except `null_query`) |

**Concrete examples (one per type):**

- **inference** (3 evidence docs) — *"Who is the individual associated with the cryptocurrency
  industry facing a criminal trial on fraud and conspiracy charges, as reported by both The Verge
  and TechCrunch…?"* → **Sam Bankman-Fried**
- **comparison** (2 evidence docs) — *"Do the TechCrunch article on software companies and the Hacker
  News article on The Epoch Times both report an increase in revenue related to payment and
  subscription models…?"* → **Yes**
- **temporal** (2 evidence docs) — *"After the TechCrunch report on October 7, 2023 … and the
  subsequent article on October 30, 2023 … was there a change in the nature of the events?"* → **Yes**
- **null** (0 evidence docs) — a plausible-sounding question whose facts aren't in the corpus →
  **Insufficient information.**

### Relevance labels (qrels)

- Relevance is **document-level**: a query's gold docs are the `title`s in its `evidence_list`.
- Titles are unique and resolve to the corpus **100%** (6,084 / 6,084 evidence references matched).
- Answerable queries have **min 2, max 4, avg 2.7** evidence docs.
- **`null_query` (301) is excluded** from retrieval scoring — with no relevant docs, retrieval is undefined.

---

## 4. The five configs (each adds to the previous)

| # | Config | What it does |
|---|---|---|
| 1 | **Dense only** | `text-embedding-3-large` semantic vector search; chunk hits collapsed to best-ranked doc |
| 2 | **Dense + sparse** | add `bm25`; combine by **normalized score fusion** (each branch's scores scaled to its max, then summed) |
| 3 | **Hybrid RRF** | fuse the dense and sparse rank lists by **Reciprocal Rank Fusion** (`k=60`) |
| 4 | **+ Metadata-aware** | *structured-knowledge analog for this corpus.* A deterministic boost over the RRF candidate head: reward docs whose metadata is consistent with the query — matched **source** name (+1.0), **category** (+0.4), **title↔query entity overlap** (up to +1.2, proportional), shared **year** (+0.5) and **month** (+0.5) for temporal cues. Added to normalized RRF score at weight `0.5`, then re-sorted. No LLM. |
| 5 | **+ LLM rerank** | `gpt-4.1-mini` listwise reorder of the top `CAND=10` candidates (numbered candidates → model returns ranked numbers) |

> **Why metadata stands in for "structured knowledge":** our KB's structured config boosts the CWE
> `child-of` hierarchy, but MultiHop-RAG has no ontology. It *does* ship rich document metadata and is
> explicitly designed for metadata-aware multi-hop retrieval, so metadata consistency is the faithful,
> same-intent analog (structure improves ranking) on this corpus.

---

## 5. Metrics (all @10, document-level)

- **MRR@10** — reciprocal rank of the *first* relevant doc (rewards getting one right answer to the top).
- **MAP@10** — mean average precision over a query's relevant docs (rewards ranking *all* evidence high).
- **Recall@10** — fraction of a query's evidence docs found in the top 10 (coverage — key for multi-hop).
- **Hits@10** — 1 if *any* relevant doc is in the top 10 (did retrieval find *something* useful).

These are MultiHop-RAG's headline retrieval metrics, so numbers are comparable to its leaderboard.

---

## 6. How to run

```powershell
cd skill-factory\benchmarks\multihop_rag

# one-time: build the isolated index (needs AZURE_API_KEY for dense embeddings)
python index.py                       # -> 609 docs / 5144 chunks in ./qdrant

# run the ablation (stratified sample; default 300 queries)
$env:ABLATION_N = "300"
python ablation.py                    # -> prints table, writes ablation_results.json
```

- **Env:** `AZURE_API_KEY` required; `ABLATION_N` sets the sample size (default 300; set higher / omit
  to run all 2,255).
- **Sampling:** queries are **stratified by `question_type`** (proportional) with a fixed seed (13) for
  a representative, reproducible slice. The expensive part is the LLM reranker (one `gpt-4.1-mini` call
  per query), so the default caps at 300.
- **Isolation:** uses its own `./qdrant` store — the KB service on `:8900` can keep running. (Unlike
  `kb/ablation.py`, which opens `kb_data/qdrant` directly and requires the service stopped.)

### Files

```
benchmarks/multihop_rag/
  README.md              # this file
  index.py               # chunk + embed corpus -> ./qdrant (collection "multihop")
  ablation.py            # 5-config study, metrics @10, writes ablation_results.json
  data/
    corpus.json          # 609 docs (from HuggingFace)
    MultiHopRAG.json     # 2556 queries + evidence (from HuggingFace)
  qdrant/                # isolated local vector store (generated)
  ablation_results.json  # latest run output
  ablation_run_300.log   # latest run log
```

---

## 7. Results (full 2,255 answerable queries, @10)

| Config | MRR@10 | MAP@10 | Recall@10 | Hits@10 |
|---|---|---|---|---|
| Dense only | 0.781 | 0.584 | 82.2% | 98.8% |
| Dense + sparse | 0.821 | 0.635 | 84.4% | 99.4% |
| Hybrid RRF | 0.808 | 0.617 | 84.2% | 99.4% |
| + Metadata-aware | 0.797 | 0.645 | 88.2% | 99.7% |
| **+ LLM rerank** | **0.858** | **0.695** | **88.2%** | **99.7%** |

*(A 300-query stratified slice gave the same ordering and near-identical values — the full run
moved every number by < 0.03, so the conclusions are stable.)*

### Findings

- **Dense is a strong floor** — news retrieval is easy for a good embedder (0.77 MRR), so headroom is small.
- **Sparse helps here** (+0.04 MRR, +0.05 MAP, +2 pts recall). MultiHop queries name proper nouns
  (people, companies, products), so BM25 exact-term matching adds signal. **This is the opposite of the
  CWE ablation**, where long descriptive queries made sparse *hurt* — same architecture, opposite
  behavior, explained by query style.
- **RRF is level-to-slightly-below plain normalized fusion** (0.808 vs 0.821 MRR) — not the layer doing the work.
- **Metadata-aware is a trade-off:** it lifts **Recall@10 to 88.2% and Hits@10 to 99.7%** (pulls more of
  the 2–4 evidence docs into the top-10) but drops MRR below dense+sparse (it reshuffles the #1 slot).
- **LLM rerank is the MVP** — best on every metric (MRR 0.858, MAP 0.695). It recovers the top-rank
  precision the metadata step gave up while keeping the recall gain; metadata + rerank work as a pair.

**Bottom line:** full stack vs. dense-only lifts **MAP@10 0.584 → 0.695 (+19% rel.)**, **Recall@10
82.2% → 88.2%**, **MRR 0.781 → 0.858**. Every layer earns its place except RRF-vs-fusion (a wash), and
metadata only pays once rerank follows it. Combined with the CWE study, the design justification is:
**keep hybrid dense+sparse + rerank — each component's value is query-type-dependent (sparse helps
entity queries, hurts descriptive ones), but LLM reranking helps universally and is the single
strongest addition in both benchmarks.**

### Caveats

- Scored on the **full 2,255 answerable queries** (the entire non-null set); a seed-13 300-query
  stratified slice reproduced the same ordering and values.
- Metric granularity is **doc-level** (evidence titles), matching the dataset's labels.
- `null_query` distractors are excluded (no retrieval target); evaluating abstention would need the QA stage.

## 8. Comparison to the original paper (and why numbers differ)

The MultiHop-RAG paper (Table 5) reports much lower absolute numbers — e.g. best embedder
`bge-large-en-v1.5` at **MRR@10 0.430 / MAP@10 0.342 / Hits@10 0.672**, and the best *reranked* config
`voyage-02 + bge-reranker-large` at **MRR@10 0.586 / MAP@10 0.480 / Hits@10 0.747**. Our numbers are
**not directly comparable** for two reasons:

1. **Relevance granularity (the main one).** Their `retrieval_evaluate.py` scores at the **fact-passage
   level via substring match** — a retrieved chunk counts only if it *contains the exact gold evidence
   excerpt*. We score at the **document level** — a hit if any chunk of the correct article (title match)
   is retrieved. Ours is the easier "find the right document"; theirs is "find the passage with the
   specific fact." That explains most of the gap.
2. **Newer models.** We use `text-embedding-3-large` + `gpt-4.1-mini` reranker; they tested
   ada-002 / bge / voyage + `bge-reranker-large`.

**What agrees:** in both, the **reranker is the single biggest lever** — their bge-reranker adds
+0.13 to +0.19 MRR across every embedder; our rerank layer is likewise the top performer. A true
head-to-head would require switching this harness to the paper's fact-substring, passage-level scoring.
