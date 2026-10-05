"""Skill-level optimization: iterate on the skill artifact itself to make it more general.

Per epoch, on a batch of related instances:
  forward   - run the skill tool-free on the batch and score it
  gradient  - an LLM proposes general, portable fixes and names missing knowledge; it sees the
              skill, aggregate metrics, and the batch inputs, never the ground truth
  enrich    - fetch the missing knowledge from the KB
  step      - regenerate an improved skill folding in the fixes
Keep the best skill on the optimize batch, certify it once on an untouched test batch, and store it
only if it clears the bar. Seed / optimize / test sets are disjoint, and the ground truth is only
ever used by the scorer.
"""
import json
import os
import re
from pathlib import Path

from deduct import deduct
from induct import (INDUCTION_SYSTEM, INDUCT_MAX_TOKENS, induct, load_trace, render_skill_md,
                    save_skill, skill_from_dict, write_skill_package)
from kb_client import search_docs
from llm import DISTILL_MODEL, JUDGE_MODEL, chat
from score import rubric_score
from store import register_in_router

WORKSPACES = Path(__file__).resolve().parent.parent / "workspaces"
RUBRIC_MIN = 0.70
GRAD_MAX_TOKENS = int(os.getenv("GRAD_MAX_TOKENS", "16000"))   # regenerated skill grows as knowledge folds in


def _json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


def _refs_text(skill) -> str:
    return "\n\n".join(f"# {r.get('filename')}\n{str(r.get('content', ''))}" for r in skill.references)


# --------------------------------------------------------------------------- forward
EVAL_RETRIES = int(os.getenv("EVAL_RETRIES", "2"))


def evaluate(skill, md: str, rows: list, evaluator, ded_id: str, timeout: int = 1200) -> dict:
    """Tool-free run of the skill on `rows`: stage inputs + the skill package, deduct with NO KB, then
    score objectively vs the held-out GT. RETRIES if the agent produced predictions for too few rows -
    that is a failed run (e.g. it ran out of steps before writing output), not real skill feedback, so
    it must not pollute the gradient with a spurious 0.0."""
    s = None
    for attempt in range(EVAL_RETRIES + 1):
        did = ded_id if attempt == 0 else f"{ded_id}r{attempt}"
        evaluator.stage(rows, did)                                   # writes input.tsv + holds GT
        write_skill_package(skill, md, WORKSPACES / did / "skill")   # SKILL.md + references/
        deduct(evaluator.task(len(rows)), did, timeout_s=timeout, no_kb=True)
        s = evaluator.score(did)
        if evaluator.produced(did, len(rows)):
            return s
        print(f"    (eval produced too few predictions - failed run; retry {attempt + 1}/{EVAL_RETRIES})", flush=True)
    return s


# --------------------------------------------------------------------------- gradient
def diagnose_gradient(md: str, refs_text: str, score: dict, input_descriptions: str) -> tuple[str, list]:
    """GENERAL, portable fix instructions + topic queries for MISSING knowledge. Sees inputs + metrics,
    NEVER the ground truth."""
    prompt = (
        "A PORTABLE skill was used by an agent with NO special tools on a SAMPLE batch drawn from a task "
        "FAMILY, and underperformed. Your goal is to make the skill's knowledge COMPREHENSIVE and GENERAL "
        "for the WHOLE family - do NOT merely patch the cases in this batch.\n\n"
        f"AGGREGATE RESULT (no per-item answers): score={score.get('value')} "
        f"precision={score.get('avg_precision')} recall={score.get('avg_recall')}.\n"
        "Low recall => the bundled knowledge is too NARROW (whole areas of the domain are missing) or the "
        "rules are too conservative. Low precision => it asserts unsupported items.\n\n"
        f"SKILL.md:\n{md[:3000]}\n\nBUNDLED REFERENCE KNOWLEDGE (excerpt):\n{refs_text[:3500]}\n\n"
        f"A SAMPLE of task inputs - use ONLY to recognize the family and its domain/style; do NOT limit "
        f"coverage to the specific behaviors they mention:\n{input_descriptions[:2500]}\n\n"
        'Return JSON {"diagnosis": "...", "kb_queries": ["...", ...]} where:\n'
        "- diagnosis: GENERAL, PORTABLE guidance usable by ANY standalone agent on ANY system. Do NOT "
        "mention any tool/service/system or any specific input or answer. Push the skill toward "
        "COMPREHENSIVE coverage of the ENTIRE task family so it generalizes to UNSEEN instances, not just "
        "the ones observed.\n"
        "- kb_queries: topic phrases for building a COMPREHENSIVE knowledge base spanning the WHOLE domain "
        "of this family. Infer the family's full scope from the skill's description, ENUMERATE its major "
        "areas/dimensions, and query for each - INCLUDING areas the current sample did not exercise. "
        "General topics, never instance-specific."
    )
    d = _json(chat([{"role": "user", "content": prompt}], model=JUDGE_MODEL, json_mode=True, max_tokens=900))
    return str(d.get("diagnosis", "")), [str(q) for q in (d.get("kb_queries") or [])][:12]


def kb_enrich(queries: list) -> str:
    """Pull grounded/verified knowledge for the missing topics from the KB (build-time source)."""
    blocks, seen = [], set()
    for q in queries:
        for hit in search_docs(q, doc_type="attack-technique", k=5):
            cit = str(hit.get("citation", "")).strip()
            key = cit[:60]
            if not cit or key in seen:
                continue
            seen.add(key)
            blocks.append(f"- {cit}: {str(hit.get('text', ''))[:180]}")
    return "\n".join(blocks[:40])


# --------------------------------------------------------------------------- optimizer step
def apply_gradient(diagnosis: str, retrieved: str, cur_md: str, cur_refs_text: str):
    """Regenerate an improved, still-portable skill package that folds in the gradient + verified
    knowledge. Reuses the induction portability contract."""
    # size policy: default compacts/dedups; EXPAND_UNCAPPED=1 carries all related knowledge verbatim
    if os.getenv("EXPAND_UNCAPPED", "0") != "0":
        size_rule = ("Incorporate EVERY provided knowledge item as its own explicit reference row - do NOT "
                     "drop, sample, summarize away, or collapse items to stay short; deduplicate only exact "
                     "duplicates. Completeness of coverage takes priority over brevity; the reference may be large.")
    else:
        size_rule = ("Keep the bundled reference COMPACT and DEDUPLICATED: MERGE the new knowledge into the "
                     "existing lookup tables (do not append verbatim or duplicate rows), prefer terse table "
                     "rows over prose, and keep the total reference well under ~180 mapping rows.")
    prompt = (
        "Improve the PORTABLE skill below so an agent with NO special tools performs better across this "
        "task family. Apply the diagnosis and FOLD IN the verified knowledge to build a COMPREHENSIVE, "
        "GENERAL reference for the ENTIRE task family - cover the whole domain so it handles UNSEEN "
        "instances, not only the cases that just failed; loosen over-conservative rules that suppress "
        "valid answers.\n\n"
        "STRICT - the result must stay GENERAL and PORTABLE: no tool names, no system/infrastructure, no "
        "references to any specific input or answer. Every addition must be general domain knowledge and "
        "general guidance any standalone agent can reuse.\n\n"
        f"DIAGNOSIS (what to fix):\n{diagnosis}\n\n"
        f"VERIFIED KNOWLEDGE TO INCORPORATE (grounded - do not contradict it):\n{retrieved or '(none)'}\n\n"
        f"CURRENT SKILL.md:\n{cur_md}\n\nCURRENT REFERENCES:\n{cur_refs_text}\n\n"
        f"{size_rule} Return the improved skill as JSON "
        "with the SAME schema: id, name, description, parameters, dependencies (generic capabilities "
        "only), procedure (cite references/<file> where knowledge is needed), references:[{filename, "
        "when_to_use, content}], pitfalls."
    )
    raw = chat([{"role": "system", "content": INDUCTION_SYSTEM}, {"role": "user", "content": prompt}],
               model=DISTILL_MODEL, json_mode=True, max_tokens=GRAD_MAX_TOKENS)
    return skill_from_dict(_json(raw))


# --------------------------------------------------------------------------- loop
def optimize_skill(task_id: str, evaluator, optimize_rows: list, test_rows: list,
                   epochs: int, bar: float, timeout: int = 1200) -> dict:
    trace = load_trace(task_id)
    skill = induct(trace)
    expanded_id = None
    if os.getenv("DISTILL_EXPAND_KNOWLEDGE", "0") != "0":
        from expand import expand_knowledge      # local import avoids optimize<->expand circular import
        try:
            skill = expand_knowledge(skill, trace)
            expanded_id = skill.id               # pin so optimization can't rename over the used-only skill
        except Exception as e:                   # a big/truncated weave must not nuke the run
            print(f"  [expand] weave failed ({e}); continuing with un-expanded skill", flush=True)
    md = render_skill_md(skill)
    best_skill, best_md, best_val = skill, md, -1.0
    history = []

    for ep in range(epochs):
        s = evaluate(skill, md, optimize_rows, evaluator, f"opt_{task_id[5:13]}_{ep}", timeout)
        val = float(s.get("value") or 0.0)
        history.append({"epoch": ep, "optimize": val, "precision": s.get("avg_precision"),
                        "recall": s.get("avg_recall"), "refs": len(skill.references)})
        print(f"  [opt {ep}] tool-free optimize {s.get('metric')}={val} "
              f"(prec={s.get('avg_precision')} rec={s.get('avg_recall')})", flush=True)
        if val > best_val:
            best_skill, best_md, best_val = skill, md, val
        if val >= bar:
            print("  optimize target reached -> early stop.", flush=True)
            break
        if ep == epochs - 1:
            break
        try:
            diagnosis, queries = diagnose_gradient(md, _refs_text(skill), s, evaluator.input_text(optimize_rows))
            history[-1]["kb_queries"] = queries
            retrieved = kb_enrich(queries)
            print(f"  [opt {ep}] gradient: {len(queries)} topics -> {len(retrieved.splitlines())} grounded "
                  f"facts; regenerating skill...\n    topics: {queries}", flush=True)
            new_skill = apply_gradient(diagnosis, retrieved, md, _refs_text(skill))
            skill, md = new_skill, render_skill_md(new_skill)
        except Exception as e:  # noqa: BLE001 - a bad gradient step must never nuke the run
            print(f"  [opt {ep}] gradient step failed ({e}); keeping best-so-far and stopping early.", flush=True)
            break

    # certify the best-on-optimize skill on the UNTOUCHED test set
    ts = evaluate(best_skill, best_md, test_rows, evaluator, f"opt_{task_id[5:13]}_test", timeout)
    test_val = float(ts.get("value") or 0.0)
    rubric, _ = rubric_score(best_md)
    passed = test_val >= bar and rubric >= RUBRIC_MIN
    stored = registered = None
    if passed:
        if expanded_id:                          # never overwrite the used-only skill dir
            best_skill.id = expanded_id
            best_md = render_skill_md(best_skill)
        _md_path, json_path = save_skill(best_skill, best_md)
        registered = register_in_router(json_path)
        stored = True
        print(f"  GATE PASSED -> stored '{best_skill.id}' and registered.", flush=True)
    else:
        print(f"  GATE FAILED (test {test_val} < {bar} or rubric {rubric} < {RUBRIC_MIN}) -> not stored.", flush=True)

    return {
        "skill_id": best_skill.id,
        "gate": f"held-out TEST {ts.get('metric')}>={bar} and rubric>={RUBRIC_MIN}",
        "scores": {"optimize_best": round(best_val, 3), "test": test_val, "rubric": rubric,
                   "test_precision": ts.get("avg_precision"), "test_recall": ts.get("avg_recall")},
        "epochs": history, "passed": passed, "stored": bool(stored), "registered": registered,
        "optimize_rows": len(optimize_rows), "test_rows": len(test_rows),
    }
