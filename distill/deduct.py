"""Deduction: a frozen agent re-solves the task from the induced skill alone (it never sees
the original trace). The outcome is the main validation signal; the re-solve trace is also
compared to the original for a reconstruction score.

Runs the factory in a killable child process (_factory_worker.py) in the Docker executor,
UTF-8-safe on Windows pipes, with `docker rm -f` on timeout.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORKER = HERE / "_factory_worker.py"

MAX_STEPS = os.getenv("DEDUCT_MAX_STEPS", "25")


def build_deduction_task(task: str) -> str:
    return (
        f"{task}\n\n"
        "---\n"
        "A reusable SKILL for this kind of task is provided in your workspace at `skill/SKILL.md`.\n"
        "Read it first and follow its procedure. It may point to additional reference files under\n"
        "`skill/references/` - open those (with your file-reading tool) when a step tells you to.\n"
        "Rely on the skill's own instructions and bundled knowledge; assume no special tools beyond\n"
        "reading and writing files."
    )


def deduct(task: str, task_id: str, timeout_s: int = 1200, no_kb: bool = True) -> tuple[dict | None, str]:
    """Run the frozen factory agent on the task, with the skill staged as files in its workspace
    (skill/SKILL.md + skill/references/). Runs in a real Docker container; when no_kb=True the agent
    gets base file tools only (WORKER_NO_KB) so passing proves the skill is self-contained/portable.
    Returns (RunResult dict, combined log); the full trace lands in traces/<task_id>.json."""
    aug = build_deduction_task(task)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(aug)
        task_file = tf.name

    env = {**os.environ, "EXECUTOR_TYPE": "docker", "FACTORY_MAX_STEPS": str(MAX_STEPS),
           "FACTORY_TIMEOUT_S": str(timeout_s), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    if no_kb:
        env["WORKER_NO_KB"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER), task_file, task_id],
            capture_output=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", f"skill-factory-{task_id}"], capture_output=True)
        return {"status": "timeout"}, "deduction timed out"

    result = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("RESULT_JSON:"):
            try:
                result = json.loads(line[len("RESULT_JSON:"):])
            except json.JSONDecodeError:
                pass
    log = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return result, log
