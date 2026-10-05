"""Distillation pipeline: trace -> validated, stored skill.

  induct  -> SKILL.md (generalized)
  deduct  -> a frozen agent re-solves the task from the skill only           [--validate]
  score   -> reconstruction + outcome + rubric
  refine  -> feed the critique back into induction, keep the best            [--iters N]
  gate    -> store only if it clears the thresholds
  store   -> write SKILL.md + register it in the router

Usage:
  python pipeline.py <task_id>                 # full validated loop (runs the factory)
  python pipeline.py <task_id> --no-validate   # induct + rubric gate only (fast, no factory)
  python pipeline.py <task_id> --iters 2       # up to 2 refinement passes
  python pipeline.py <task_id> --no-store      # don't register in the router
"""
import argparse
import os
import sys
from pathlib import Path

from deduct import deduct
from induct import induct, load_trace, render_skill_md, save_skill, write_skill_package
from llm import DISTILL_MODEL
from score import build_feedback, outcome_score, reconstruction_score, rubric_score
from store import register_in_router

RUBRIC_MIN = 0.70
OUTCOME_MIN = 0.60
WORKSPACES = Path(__file__).resolve().parent.parent / "workspaces"
DEDUCT_NO_KB = os.getenv("DEDUCT_NO_KB", "1") != "0"   # verify portability with base file tools only
# opt-in: after induction, expand each used knowledge item to its related KB cluster (default off)
EXPAND_KNOWLEDGE = os.getenv("DISTILL_EXPAND_KNOWLEDGE", "0") != "0"


def _overall(validate: bool, recon: float, outcome: float, rubric: float) -> float:
    if validate:
        return round(0.5 * outcome + 0.3 * rubric + 0.2 * recon, 3)
    return rubric


def distill(task_id: str, iters: int = 1, validate: bool = True, store: bool = True,
            bench_hook=None, outcome_min: float = OUTCOME_MIN) -> dict:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    trace = load_trace(task_id)
    orig_task = trace["run"]["task"]
    orig_final = trace["run"].get("final_answer")
    # bench_hook (labelled tasks, test harness only): verify the induced skill on a HELD-OUT
    # slice of instances the skill was NOT induced from, scored objectively. A memorized skill
    # cannot pass - it must generalize. `ded_task` is the hook's own generic task text (no
    # retrieve nudge). When absent, this is the generic open-task path (unchanged).
    ded_task = bench_hook.task if bench_hook else orig_task

    best = None
    feedback = ""
    attempts = []

    for i in range(iters + 1):
        print(f"\n=== induction pass {i} (model={DISTILL_MODEL}) ===", flush=True)
        skill = induct(trace, feedback=feedback)
        if EXPAND_KNOWLEDGE:
            from expand import expand_knowledge      # local import: only when the flag is on
            skill = expand_knowledge(skill, trace)
        md = render_skill_md(skill)

        recon = outcome = 0.0
        out_note = ""
        if validate:
            ded_id = f"ded_{task_id[5:13]}_{i}"
            if bench_hook:
                bench_hook.stage(ded_id)   # stage the held-out rows for the frozen re-solve
            write_skill_package(skill, md, WORKSPACES / ded_id / "skill")   # stage the skill as files
            print(f"  deducting (tool_free={DEDUCT_NO_KB}): frozen agent re-solves via skill only ({ded_id})...", flush=True)
            ded_result, _log = deduct(ded_task, ded_id, no_kb=DEDUCT_NO_KB)
            try:
                ded_trace = load_trace(ded_id)
                recon = reconstruction_score(trace, ded_trace)
            except FileNotFoundError:
                recon = 0.0
            if bench_hook:
                outcome, out_note = bench_hook.score(ded_id)   # objective score on unseen rows
            else:
                outcome, out_note = outcome_score(orig_task, orig_final, ded_result)

        rubric, critique = rubric_score(md)
        overall = _overall(validate, recon, outcome, rubric)
        cand = {
            "pass": i, "skill": skill, "md": md,
            "reconstruction": recon, "outcome": outcome, "rubric": rubric,
            "overall": overall, "out_note": out_note, "critique": critique,
        }
        attempts.append({k: cand[k] for k in ("pass", "reconstruction", "outcome", "rubric", "overall")})
        print(f"  scores: reconstruction={recon} outcome={outcome} rubric={rubric} -> overall={overall}", flush=True)

        if best is None or overall > best["overall"]:
            best = cand
        if i < iters:
            feedback = build_feedback(critique, out_note, recon, outcome, rubric)

    # ---- verification gate ----
    if validate:
        passed = best["outcome"] >= outcome_min and best["rubric"] >= RUBRIC_MIN
        scope = "held-out outcome" if bench_hook else "outcome"
        gate_desc = f"{scope}>={outcome_min} and rubric>={RUBRIC_MIN}"
    else:
        passed = best["rubric"] >= RUBRIC_MIN
        gate_desc = f"rubric>={RUBRIC_MIN} (no deduction validation)"

    report = {
        "task_id": task_id, "validated": validate, "gate": gate_desc,
        "best_pass": best["pass"], "scores": {k: best[k] for k in ("reconstruction", "outcome", "rubric", "overall")},
        "passed": passed, "attempts": attempts, "skill_id": best["skill"].id, "stored": False,
    }

    if passed and store:
        md_path, json_path = save_skill(best["skill"], best["md"])
        registered = register_in_router(json_path)
        report["stored"] = True
        report["skill_md"] = str(md_path)
        report["registered"] = registered
        print(f"\nGATE PASSED -> stored '{best['skill'].id}' and registered in router.", flush=True)
    elif passed:
        md_path, json_path = save_skill(best["skill"], best["md"])
        report["skill_md"] = str(md_path)
        print(f"\nGATE PASSED -> saved '{best['skill'].id}' (router registration skipped: --no-store).", flush=True)
    else:
        print(f"\nGATE FAILED ({gate_desc}) -> skill NOT stored.", flush=True)

    return report


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id")
    ap.add_argument("--iters", type=int, default=1, help="refinement passes after the first induction")
    ap.add_argument("--no-validate", action="store_true", help="skip deduction; gate on rubric only")
    ap.add_argument("--no-store", action="store_true", help="do not register the skill in the router")
    args = ap.parse_args()

    import json as _json
    rep = distill(args.task_id, iters=args.iters, validate=not args.no_validate, store=not args.no_store)
    print("\n" + _json.dumps(rep, indent=2))
