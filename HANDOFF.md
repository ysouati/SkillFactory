# Handoff

## Problem

Agents are generalists. On cyber tasks they often guess. A skill (a file with a procedure
and the knowledge for one kind of task) makes an agent reliable at that task. Today skills
are written by hand and go stale. There is no system that creates and maintains them.

## Solution

A system that builds skills from solved tasks and reuses them. Seven stages: Route, Solve,
Retrieve, Distill, Validate, Store, Improve. A skill is a portable package (a `SKILL.md` plus
reference files) that any agent can follow without this system's tools, because the knowledge
the tools returned is written into the references.

## What has been done

Stages 1 to 6 are built and run end to end. Stage 7 (Improve) is not built.

Components:
- `router/`: embed the task, search stored skill descriptions, judge whether to reuse a skill
  or build one.
- `factory/`: a smolagents CodeAgent that solves tasks, in a Docker sandbox or locally, with
  file, shell, and KB tools. Includes the Solve to Retrieve to Verify to Refine loop.
- `kb/`: ATT&CK, CWE, and NIST reference data in a fact store (SQLite) and a prose store
  (Qdrant, hybrid dense plus BM25 plus rerank), served over HTTP on port 8900.
- `distill/`: induct a trace into a `SKILL.md`, re-solve held-out rows with the skill alone
  (deduct), score, optimize the skill against a set with KB-grounded enrichment, and store it.

Models run on Azure OpenAI. Defaults: `gpt-5.4` for solving and induction, `gpt-4.1-mini` for
judging, `text-embedding-3-large` for embeddings. Set `AZURE_API_KEY` and `AZURE_BASE_URL`.
Override model names with the env vars listed in the README.

- Portable skills are validated tool-free on held-out rows the skill was not built from, so a
  skill that memorizes its training trace cannot pass.

## Results

- A distilled skill helps a weak model and is flat for a strong model. On ATT&CK technique
  extraction, gpt-4.1-mini went from 0 to about 0.26 F1 with a skill (p < 0.001); gpt-5.4
  stayed within noise (about plus or minus 0.03). Measured with a paired same-session A/B,
  which is the reliable design here because the weak model's baseline is noisy run to run.
- Adding more related knowledge to a skill did not change accuracy. A 112 KB skill matched the
  34 KB one on the held-out test (0.672 F1) and ran about 45 times slower per batch.
- Benchmarks: CVE to CWE 72.8 percent baseline, 74.4 percent with a confidence-gated KB check.
  ATT&CK technique extraction about 0.6 F1 (the CTIBench GPT-4 result is 0.64).
- Small local models (1B to 4B via Ollama) could not follow the agent protocol on a 4 GB GPU.

## Open items

- Stage 7 (Improve): repair skills from accumulated successes and failures.
- Store gate: gate on the skill beating the no-skill baseline on the same held-out set. The
  current gate is an absolute threshold.
- Close the loop: when the router matches a skill, execute the stored package. It currently
  reports the match.
- Skill granularity and composition: for a complex task, decide when to split it into smaller
  skills that a parent skill composes. Open design question.

## Running it

See `README.md` for setup, KB build, and run commands.



`For more details, check the Skill Factory PDF in this repo`