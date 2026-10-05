"""Solve -> Retrieve -> Verify -> Refine loop (the front-end to distillation).

Per attempt:
  feed     - benchmark task: strip the ground truth and stage a description-only input.tsv;
             open-ended task: pass the task + success criteria as-is
  retrieve - the agent pulls prior failed attempts (each with an outcome and a diagnosis)
  solve    - the factory, in a Docker container, with KB tools on
  verify   - benchmark: recompute the metric against the held-out ground truth;
             open-ended: check the success criteria (over_budget / timeout counts as failure)
  refine   - on failure, write a diagnosis (from the approach + aggregate outcome, never the
             ground truth) and index the failed attempt so the next one can retrieve it

Run:  python solve_loop.py
Env:  AZURE_API_KEY, Docker, KB service on :8900.
      LOOP_ATTEMPTS(3) LOOP_TIMEOUT(1500) LOOP_MAX_STEPS(25) HB_N(15) HB_BAR(0.65)
"""
import json
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from openai import OpenAI

from bench_tasks import BENCHES, build_task, load_rows, meets, read_predictions, stage_input
from settings import AZURE_BASE_URL, get_api_key
from verify import build_evidence, verify_trace

ROOT = Path(__file__).parent.parent
TRACES = ROOT / "traces"
WORKER = ROOT / "distill" / "_factory_worker.py"
DISTILL_WORKER = ROOT / "distill" / "_distill_worker.py"
KB_URL = os.getenv("KB_URL", "http://localhost:8900")
DIAG_MODEL = os.getenv("DIAG_MODEL", "gpt-4.1-mini")

MAX_STEPS = os.getenv("LOOP_MAX_STEPS", "25")
TIMEOUT = int(os.getenv("LOOP_TIMEOUT", "1500"))
MAX_ATTEMPTS = int(os.getenv("LOOP_ATTEMPTS", "3"))
DISTILL_TIMEOUT = int(os.getenv("LOOP_DISTILL_TIMEOUT", "7200"))   # optimizer runs several tool-free deductions
DISTILL_HELDOUT = os.getenv("LOOP_DISTILL_HELDOUT", "10")

RETRIEVE_NUDGE = (
    "BEFORE you start, call search_prior_solves with a short description of this task to retrieve "
    "PRIOR ATTEMPTS at it - including past FAILURES, each carrying an 'outcome' (how it scored) and "
    "a 'diagnosis' of what went wrong. Read them: do NOT repeat those mistakes, and build on the "
    "best-scoring prior approach. Then solve."
)


@dataclass
class TaskSpec:
    kind: str                 # "benchmark" | "open"
    prefix: str
    bench_name: str = ""      # benchmark: ate/mcq/vsp
    n: int = 0
    bar: float = 0.0
    task: str = ""            # open
    criteria: str = ""


# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _llm() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL,
                  timeout=float(os.getenv("DIAG_LLM_TIMEOUT", "180")), max_retries=3)


def run_factory(task: str, task_id: str) -> dict:
    """One real-factory Docker solve in a killable subprocess (KB tools available)."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(task)
        tfp = tf.name
    env = {**os.environ, "EXECUTOR_TYPE": "docker", "FACTORY_MAX_STEPS": str(MAX_STEPS),
           "FACTORY_TIMEOUT_S": str(TIMEOUT), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run([sys.executable, str(WORKER), tfp, task_id],
                              capture_output=True, encoding="utf-8", errors="replace",
                              cwd=str(ROOT), timeout=TIMEOUT, env=env)
        for line in (proc.stdout or "").splitlines():
            if line.startswith("RESULT_JSON:"):
                return json.loads(line[len("RESULT_JSON:"):])
        return {"status": "error", "error": (proc.stdout or "")[-300:] + (proc.stderr or "")[-300:]}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", f"skill-factory-{task_id}"], capture_output=True)
        return {"status": "timeout"}


def _load_trace(task_id: str) -> dict | None:
    p = TRACES / f"{task_id}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def llm_diagnose(task: str, approach: str, outcome: str, status: str) -> str:
    """Method-level 'what went wrong' from the approach + AGGREGATE outcome only. No GT, no
    per-row correctness -> leakage-safe."""
    prompt = (
        "An agent attempted the task below and did NOT pass. In 2-4 sentences, diagnose WHAT went "
        "wrong and WHAT to do differently next time. Base it ONLY on the approach and the aggregate "
        "outcome - you do NOT have the ground truth, so give method-level guidance (what to search, "
        "what to check, where it was too shallow or too broad), never specific answers.\n\n"
        f"TASK:\n{task[:800]}\n\nOUTCOME: {outcome}\nSOLVE STATUS: {status}\n\n"
        f"APPROACH IT TOOK:\n{approach[:3000]}\n\nDiagnosis:"
    )
    try:
        r = _llm().chat.completions.create(
            model=DIAG_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0, max_completion_tokens=250)
        return (r.choices[0].message.content or "").strip()
    except Exception as e:  # noqa: BLE001
        return f"(diagnosis unavailable: {e})"


def run_distillation(spec: "TaskSpec", task_id: str) -> dict:
    """On an accepted trace: induct a generalized skill, then VERIFY it by having a frozen agent
    re-solve HELD-OUT rows (docker) with only that skill and scoring them objectively; store it
    if it clears the gate. Runs in a killable subprocess (isolated distill/ sys.path)."""
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    if spec.kind == "benchmark":
        env.update({"DISTILL_BENCH": spec.bench_name, "DISTILL_BENCH_N": str(spec.n),
                    "DISTILL_BENCH_HELDOUT": str(DISTILL_HELDOUT), "DISTILL_BENCH_BAR": str(spec.bar)})
    try:
        proc = subprocess.run([sys.executable, str(DISTILL_WORKER), task_id],
                              capture_output=True, encoding="utf-8", errors="replace",
                              cwd=str(ROOT / "distill"), timeout=DISTILL_TIMEOUT, env=env)
        for line in (proc.stdout or "").splitlines():
            if line.startswith("DISTILL_JSON:"):
                return json.loads(line[len("DISTILL_JSON:"):])
        return {"error": ((proc.stdout or "")[-500:] + (proc.stderr or "")[-500:]).strip()}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "ps", "-q", "--filter", "name=skill-factory-ded_"],
                       capture_output=True)
        return {"error": "distillation timed out"}


def add_experience(task: str, ref_id: str, status: str, approach: str, outcome: str, diagnosis: str) -> None:
    """POST one failed attempt into the experience store (the service holds the Qdrant lock)."""
    body = json.dumps({"task": task, "ref_id": ref_id, "status": status,
                       "approach": approach, "outcome": outcome, "diagnosis": diagnosis}).encode()
    try:
        req = Request(KB_URL + "/add_experience", data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=60) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        print(f"  (warning: could not index failed attempt: {e})", flush=True)


# ---------------------------------------------------------------------------
def run_loop(spec: TaskSpec) -> dict:
    if spec.kind == "benchmark":
        cfg = BENCHES[spec.bench_name]
        rows = load_rows(spec.bench_name, spec.n)
        core_task = build_task(cfg, spec.n, solving=True)
    else:
        cfg = None
        core_task = spec.task + "\n\nSuccess criteria:\n" + spec.criteria

    attempts = []
    for i in range(MAX_ATTEMPTS):
        task_id = f"{spec.prefix}_a{i}_{uuid.uuid4().hex[:4]}"
        print(f"\n{'=' * 62}\nATTEMPT {i + 1}/{MAX_ATTEMPTS}  ({task_id})", flush=True)

        gt = stage_input(cfg, rows, task_id) if spec.kind == "benchmark" else None   # FEED: strip GT
        full = core_task + "\n\n" + RETRIEVE_NUDGE                                    # RETRIEVE nudge
        res = run_factory(full, task_id)                                             # SOLVE
        trace = _load_trace(task_id)
        approach = build_evidence(trace) if trace else ""
        solve_ok = res.get("status") == "success"

        # VERIFY
        if spec.kind == "benchmark":
            preds = read_predictions(task_id)
            score = cfg.scorer(preds, gt)
            accepted = solve_ok and meets(cfg, score.get("value"), spec.bar)
            direction = ">=" if cfg.higher_better else "<="
            outcome = (f"{score.get('metric')}={score.get('value')} (target {direction} {spec.bar}); "
                       f"prec={score.get('avg_precision')} rec={score.get('avg_recall')} preds={len(preds)}")
            metric_str = f"{score.get('metric')}={score.get('value')}"
        else:
            verdict = verify_trace(spec.task, spec.criteria, res.get("final_answer"), trace) if trace else None
            accepted = solve_ok and bool(verdict and verdict.met)
            outcome = ("; ".join(f"{c.criterion[:35]}:{'PASS' if c.passed else 'FAIL'}"
                                 for c in verdict.checklist) if verdict else "no verdict")[:400]
            metric_str = "verify.met" if accepted else "criteria unmet"

        print(f"  solve={res.get('status')} | verify: {metric_str} | accepted={accepted}", flush=True)
        attempts.append({"attempt": i, "task_id": task_id, "solve_status": res.get("status"),
                         "outcome": outcome, "accepted": accepted})

        if accepted:
            print(f"\nACCEPTED on attempt {i + 1}. Distilling -> optimizing the skill + certifying on held-out TEST...", flush=True)
            dist = run_distillation(spec, task_id)
            if "error" in dist:
                print(f"  distillation error: {dist['error'][:400]}", flush=True)
            else:
                sc = dist.get("scores", {})
                print(f"  skill '{dist.get('skill_id')}' | gate: {dist.get('gate')}", flush=True)
                if dist.get("mode") == "textgrad-optimize":
                    for e in dist.get("epochs", []):
                        print(f"    epoch {e.get('epoch')}: optimize={e.get('optimize')} "
                              f"(prec={e.get('precision')} rec={e.get('recall')}) refs={e.get('refs')}", flush=True)
                    print(f"  optimize_best={sc.get('optimize_best')} | held-out TEST={sc.get('test')} "
                          f"(prec={sc.get('test_precision')} rec={sc.get('test_recall')}) rubric={sc.get('rubric')} "
                          f"-> passed={dist.get('passed')} stored={dist.get('stored')}", flush=True)
                else:
                    print(f"  held-out verify: outcome={sc.get('outcome')} rubric={sc.get('rubric')} "
                          f"recon={sc.get('reconstruction')} overall={sc.get('overall')} "
                          f"-> passed={dist.get('passed')} stored={dist.get('stored')}", flush=True)
            return {"outcome": "accepted", "winning_attempt": i, "attempts": attempts, "distillation": dist}

        # REFINE: diagnose (leakage-safe) + index the failure for the next attempt to retrieve
        diagnosis = llm_diagnose(core_task, approach, outcome, res.get("status"))
        add_experience(core_task, task_id, "failed", approach, outcome, diagnosis)
        print(f"  diagnosed + indexed failure -> next attempt can retrieve it.\n  diagnosis: {diagnosis[:200]}", flush=True)

    print(f"\nEXHAUSTED after {MAX_ATTEMPTS} attempts.", flush=True)
    return {"outcome": "exhausted", "attempts": attempts}


if __name__ == "__main__":
    spec = TaskSpec(kind="benchmark", prefix="ate_loop", bench_name="ate",
                    n=int(os.getenv("HB_N", "10")), bar=float(os.getenv("HB_BAR", "0.60")))
    rep = run_loop(spec)
    out = ROOT / "benchmarks" / "solve_loop_ate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print("\n" + "=" * 62 + f"\nOUTCOME: {rep['outcome']}")
    for a in rep["attempts"]:
        print(f"  attempt {a['attempt'] + 1}: solve={a['solve_status']:<9} accepted={a['accepted']}  {a['outcome']}")
    print(f"saved -> {out}")
