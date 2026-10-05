"""Subprocess worker: run the Factory on a task, in its own process.

Isolated so the factory's modules (settings/agent/tools, its own `settings.py`)
never collide on sys.path with the distill/router/kb modules. Prints one line
`RESULT_JSON:{...}` with the RunResult so the parent can parse it; the full trace
lands in traces/<task_id>.json as usual.

usage: python _factory_worker.py <task_file> <task_id>
"""
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "factory"))

from runner import run_task  # noqa: E402

if os.getenv("WORKER_NO_KB"):
    # base tools only - no KB HTTP client (for runs where the KB service is intentionally down)
    from tools import list_files, punt_to_human, read_file, run_shell, write_file  # noqa: E402
    TOOLS = [write_file, read_file, list_files, run_shell, punt_to_human]
else:
    from tools import ALL_TOOLS  # noqa: E402
    TOOLS = ALL_TOOLS

if __name__ == "__main__":
    task = Path(sys.argv[1]).read_text(encoding="utf-8")
    task_id = sys.argv[2]
    result = run_task(task, TOOLS, task_id)
    print("RESULT_JSON:" + json.dumps(asdict(result), default=str))
