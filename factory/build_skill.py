"""Public factory API: build a new skill for a task the router couldn't match."""
from runner import RunResult, run_task
from tools import ALL_TOOLS


def build_skill(task: str) -> RunResult:
    """Solve a task in a sandboxed CodeAgent loop with budgets, trace, and review-queue routing."""
    return run_task(task, tools=ALL_TOOLS)
