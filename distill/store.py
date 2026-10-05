"""Store a validated distilled skill: write the SKILL.md + record, and register it in the
router so future matching tasks route to `use_skill` instead of rebuilding.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUTER_WORKER = HERE / "_router_worker.py"


def register_in_router(skill_json_path: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(ROUTER_WORKER), str(skill_json_path)],
        capture_output=True,
        text=True,
        cwd=str(HERE.parent),
        timeout=180,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("REGISTERED:"):
            return line[len("REGISTERED:"):]
    raise RuntimeError(f"router registration failed:\n{proc.stdout}\n{proc.stderr}")
