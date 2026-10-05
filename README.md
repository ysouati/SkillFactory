# Skill Factory

A system that builds and reuses "skills" for cyber analysis tasks. A skill is a small,
self-contained package (a `SKILL.md` plus reference files) that tells an agent how to do
one kind of task. When a new task comes in, the router checks whether a matching skill
already exists; if not, the factory solves the task, and the distillation step turns a
successful solve into a reusable skill.

The pipeline has seven stages: Route, Solve, Retrieve, Distill, Validate, Store, Improve.

## Status

Built and working:

- **Route** — embed the task, search stored skill descriptions, and judge whether to reuse
  a skill or build a new one (`router/`).
- **Solve** — a code-writing agent (smolagents `CodeAgent`) solves a task, optionally in a
  Docker sandbox, with file and shell tools (`factory/`).
- **Retrieve** — a knowledge base over MITRE ATT&CK, CWE, and NIST text, served over HTTP so
  the agent can query it while solving (`kb/`).
- **Distill** — turn a successful trace into a portable skill: a generalized `SKILL.md` plus
  reference docs, with the knowledge the tools returned written into the references so the
  skill works without those tools (`distill/`).
- **Validate** — re-solve held-out instances with only the skill, score the result, and store
  the skill only if it clears a threshold.
- **Store** — write the skill to `skills/distilled/` and register it so the router can find it.

Not built yet:

- **Improve** — accumulating successes and failures over time to repair skills.

## Requirements

- Python 3.12
- An Azure OpenAI resource with chat and embedding deployments
- Docker (optional, for the sandboxed executor)

Python packages:

```
pip install -r requirements.txt
```

## Configuration

Set your Azure endpoint and key:

```bash
export AZURE_API_KEY=your-key
export AZURE_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
```

Model names default to your Azure deployment aliases and can be overridden by env var:

| Variable | Default | Used for |
|---|---|---|
| `FACTORY_MODEL` | `gpt-5.4` | the solving agent |
| `DISTILL_MODEL` | `gpt-5.4` | induction / skill generation |
| `DISTILL_JUDGE_MODEL`, `JUDGE_MODEL` | `gpt-4.1-mini` | scoring and routing judgments |
| `EMBED_MODEL` | `text-embedding-3-large` | embeddings for routing and retrieval |

The executor is `local` by default. Set `EXECUTOR_TYPE=docker` to run the agent's code in a
container (the image is built on first use).

## Build the knowledge base

The KB is reference material only — ATT&CK, CWE, and NIST text. Benchmark answers are never
loaded. Build it once:

```bash
# prose store: NIST SP 800-171 + ATT&CK Enterprise
python kb/ingestion/ingest.py

# fact store: ATT&CK entities/relations, then the CWE catalog
python kb/ingestion/attack_facts.py
python kb/ingestion/cwe_load.py
```

Data downloads from public sources on first run. The index lands in `kb_data/`.

## Run

Start the KB service (needed for any task that uses retrieval). It listens on port 8900:

```bash
python kb/service.py
```

Route a single task — reuse a skill if one matches, otherwise build one:

```bash
python orchestrator.py "Map a malware description to its MITRE ATT&CK techniques"
```

Run the solve loop on a benchmark (solve, retrieve, verify, refine):

```bash
python factory/solve_loop.py
```

It writes a trace to `traces/<task_id>.json`. Turn a successful trace into a skill:

```bash
python distill/pipeline.py <task_id>                 # induct, validate, store
python distill/pipeline.py <task_id> --no-validate   # induct + rubric check only
python distill/pipeline.py <task_id> --iters 2       # extra refinement passes
```

Stored skills appear under `skills/distilled/<skill-id>/`.

## Layout

```
router/        route a task to a skill or to the factory
factory/       the solving agent, its tools, and the solve loop
kb/            knowledge base: ingestion, stores, retrieval, HTTP service
distill/       induction, deduction, scoring, optimization, storage
skills/        seed skills and distilled skill packages
benchmarks/    datasets and benchmark drivers (CTIBench ATE, MultiHop RAG)
orchestrator.py  top-level entry: route then build
```

## Notes

- The KB service keeps one copy of the embeddings and BM25 model in memory and answers the
  agent's queries; the agent itself never holds the index.
- Distillation checks a skill on held-out instances the skill was not built from, so a skill
  that only memorizes its training trace does not pass.
