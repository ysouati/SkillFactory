"""Benchmark the solve + verify gate on real CTIBench blue-team tasks.

Acts as a security engineer: each task is TERSE (what/where, not how) and carries an
engineer-authored `success_criteria` (acceptance conditions, incl. a quantitative bar).
Each task is solved in a KILLABLE SUBPROCESS with a hard timeout (a hung Docker/kernel run
is killed and its container removed, then we move on - unlike run_task's in-thread timeout,
which cannot interrupt a truly hung agent). Then the verify gate judges the trace against
the criteria.

Run (from factory/):  python bench_verify_tasks.py
Needs AZURE_API_KEY, docker, and the KB service on :8900.
"""
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from verify import build_evidence, verify

ROOT = Path(__file__).parent.parent
TRACES = ROOT / "traces"
WORKER = ROOT / "distill" / "_factory_worker.py"
PER_TASK_TIMEOUT = int(os.getenv("BENCH_TASK_TIMEOUT", "480"))  # 8 min hard cap per task

TASKS = [
    {
        "name": "CTI-VSP",
        "task": (
            "Batch-score these CVEs for severity. TSV: "
            "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-vsp.tsv "
            "(Description = CVE text, GT = the correct CVSS v3.1 vector). Do the first 20 rows. "
            "Predict each CVE's CVSS v3.1 base score FROM THE DESCRIPTION ONLY (do not read or use "
            "the GT column when predicting) and tell me how close we are to ground truth."
        ),
        "criteria": (
            "For the first 20 CVEs, output a CVSS v3.1 base score between 0.0 and 10.0 for each. "
            "Each prediction must be made from the CVE Description only; the GT vector must NOT be "
            "read or used when predicting, only afterward for scoring. Compute the base score implied "
            "by each GT vector and report the mean absolute error between predicted and ground-truth "
            "base scores. The mean absolute error must be at most 2.0."
        ),
    },
    {
        "name": "CTI-ATE",
        "task": (
            "Map these threat-report descriptions to MITRE ATT&CK techniques. TSV: "
            "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-ate.tsv "
            "(Description = the report text, GT = correct comma-separated technique IDs). Do the "
            "first 20 rows (extract techniques FROM THE DESCRIPTION ONLY - do not read or use the GT "
            "column when predicting) and tell me how well we match the ground truth."
        ),
        "criteria": (
            "For each of the first 20 rows, output a set of MITRE ATT&CK technique IDs in T#### form. "
            "Each prediction must come from the Description only; the GT column must NOT be read or "
            "used when predicting, only afterward for scoring. Compute precision, recall, and F1 of "
            "the predicted technique set against the GT set per row, and report the averages. "
            "Average F1 must be at least 0.3."
        ),
    },
    {
        "name": "CTI-MCQ",
        "task": (
            "Answer these CTI multiple-choice questions. TSV: "
            "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-mcq.tsv "
            "(Question plus columns 'Option A'..'Option D', GT = the correct letter). Do the first "
            "25 rows (answer FROM THE QUESTION AND OPTIONS ONLY - do not read or use the GT column "
            "when answering) and report accuracy."
        ),
        "criteria": (
            "Answer each of the first 25 questions with a single option letter A, B, C, or D. "
            "Each answer must be produced from the question and options only; the GT column must NOT "
            "be read or used when answering, only afterward for scoring. Report exact-match accuracy "
            "against the GT column. Accuracy must be at least 70%."
        ),
    },
]


def solve(full_task: str, task_id: str, timeout: int) -> dict:
    """Run the factory in a killable subprocess. On hang -> kill + remove container."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(full_task)
        task_file = tf.name
    env = {**os.environ, "EXECUTOR_TYPE": "docker", "FACTORY_TIMEOUT_S": str(timeout),
           # force UTF-8 in the child: piped stdio defaults to cp1252 on Windows, which
           # makes smolagents' send_tools() raise UnicodeEncodeError on non-ascii tool text
           "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER), task_file, task_id],
            capture_output=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=timeout, env=env,
        )
        out, err = proc.stdout or "", proc.stderr or ""
        for line in out.splitlines():
            if line.startswith("RESULT_JSON:"):
                return json.loads(line[len("RESULT_JSON:"):])
        return {"status": "error", "task_id": task_id, "final_answer": None,
                "error": "no RESULT_JSON\n" + (out[-400:] + err[-400:])}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", f"skill-factory-{task_id}"], capture_output=True)
        return {"status": "timeout", "task_id": task_id, "final_answer": None,
                "error": f"hard timeout after {timeout}s (subprocess killed, container removed)"}


def main() -> None:
    results = []
    for t in TASKS:
        task_id = "bench_" + uuid.uuid4().hex[:8]
        full_task = t["task"] + "\n\nSuccess criteria:\n" + t["criteria"]
        print("=" * 70)
        print(f"SOLVING: {t['name']}  (task_id={task_id}, hard timeout {PER_TASK_TIMEOUT}s)", flush=True)
        r = solve(full_task, task_id, PER_TASK_TIMEOUT)
        print(f"  solve: status={r.get('status')} steps={r.get('steps')} "
              f"final={str(r.get('final_answer'))[:160]}", flush=True)

        evidence = ""
        try:
            trace = json.loads((TRACES / f"{task_id}.json").read_text(encoding="utf-8"))
            evidence = build_evidence(trace)
        except Exception:
            pass

        if r.get("status") == "timeout":
            v_met, v_summary, checklist = False, "solve timed out - nothing to verify", []
        else:
            v = verify(t["task"], t["criteria"], r.get("final_answer"), artifacts_summary=evidence)
            v_met, v_summary, checklist = v.met, v.summary, v.checklist
            print(f"  VERIFY: met={v.met}  ({v.summary})", flush=True)
            for c in v.checklist:
                print(f"    [{'PASS' if c.passed else 'FAIL'}] {c.criterion}\n           {c.note}", flush=True)

        results.append({
            "name": t["name"], "task": t["task"], "criteria": t["criteria"],
            "task_id": task_id, "solve_status": r.get("status"),
            "final_answer": str(r.get("final_answer"))[:800], "met": v_met, "summary": v_summary,
            "checklist": [{"criterion": c.criterion, "passed": c.passed, "note": c.note} for c in checklist],
        })

    out = ROOT / "benchmarks" / "verify_bench_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n" + "=" * 70 + "\nSUMMARY")
    for res in results:
        npass = sum(1 for c in res["checklist"] if c["passed"])
        print(f"  {res['name']:<9} solve={str(res['solve_status']):<9} met={str(res['met']):<5} "
              f"({npass}/{len(res['checklist'])} criteria)")
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
