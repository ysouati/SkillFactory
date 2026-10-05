import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutTimeout
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from smolagents import CodeAgent

from agent import build_agent, cleanup_task_container, in_workspace, make_workspace, new_task_id
from settings import (
    EXECUTOR_TYPE,
    MAX_STEPS,
    REVIEW_QUEUE_ROOT,
    WALL_CLOCK_TIMEOUT_S,
    WORKSPACE_ROOT,
)
from tools import PUNT_FILENAME
from tracing import save_trace


@dataclass
class RunResult:
    task_id: str
    task: str
    status: str
    final_answer: Any = None
    error: Optional[str] = None
    workspace: Optional[str] = None
    steps: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_s: float = 0.0
    punt_reason: Optional[str] = None
    punt_question: Optional[str] = None


def _extract_metrics(agent: CodeAgent) -> tuple[int, int, int]:
    steps = len(agent.memory.steps)
    in_tok = out_tok = 0
    for step in agent.memory.steps:
        in_tok += int(getattr(step, "input_token_count", 0) or 0)
        out_tok += int(getattr(step, "output_token_count", 0) or 0)
    if in_tok == 0 and hasattr(agent, "monitor"):
        in_tok = int(getattr(agent.monitor, "total_input_token_count", 0) or 0)
        out_tok = int(getattr(agent.monitor, "total_output_token_count", 0) or 0)
    return steps, in_tok, out_tok


def _write_waiting_entry(result: RunResult) -> Path:
    """Write a review_queue entry with status='waiting_for_human' and an empty answer field."""
    REVIEW_QUEUE_ROOT.mkdir(parents=True, exist_ok=True)
    path = REVIEW_QUEUE_ROOT / f"{result.task_id}.json"
    entry = {
        "task_id": result.task_id,
        "task": result.task,
        "status": "waiting_for_human",
        "reason": result.punt_reason,
        "question": result.punt_question,
        "human_answer": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trace": f"traces/{result.task_id}.json",
        "workspace": result.workspace,
    }
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return path


def _write_failure_entry(result: RunResult) -> Path:
    """Write a review_queue entry for a non-punt failure (error / timeout / over_budget)."""
    REVIEW_QUEUE_ROOT.mkdir(parents=True, exist_ok=True)
    path = REVIEW_QUEUE_ROOT / f"{result.task_id}.json"
    path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return path


def _read_punt_file(ws: Path) -> tuple[Optional[str], Optional[str]]:
    """Read the .punt.json signal file left by punt_to_human, if any."""
    punt_path = ws / PUNT_FILENAME
    if not punt_path.exists():
        return None, None
    try:
        data = json.loads(punt_path.read_text(encoding="utf-8"))
        return data.get("reason"), data.get("question")
    except Exception:
        return None, None


def run_task(task: str, tools: list, task_id: Optional[str] = None) -> RunResult:
    task_id = task_id or new_task_id()
    ws = make_workspace(task_id)
    (ws / PUNT_FILENAME).unlink(missing_ok=True)
    result = RunResult(task_id=task_id, task=task, status="pending", workspace=str(ws))

    agent = build_agent(tools=tools, workspace=ws)
    started = time.monotonic()

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            def _run():
                with in_workspace(ws):
                    return agent.run(task)

            future = pool.submit(_run)
            try:
                answer = future.result(timeout=WALL_CLOCK_TIMEOUT_S)
                result.final_answer = answer
                reason, question = _read_punt_file(ws)
                if reason:
                    result.status = "punted"
                    result.punt_reason = reason
                    result.punt_question = question
                else:
                    result.status = "success"
            except FutTimeout:
                result.status = "timeout"
                result.error = f"Wall-clock timeout ({WALL_CLOCK_TIMEOUT_S}s)"
    except Exception as e:
        result.status = "error"
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    finally:
        result.duration_s = round(time.monotonic() - started, 2)
        result.steps, result.input_tokens, result.output_tokens = _extract_metrics(agent)
        if result.status == "success" and result.steps >= MAX_STEPS:
            result.status = "over_budget"
            result.error = f"Max steps ({MAX_STEPS}) reached without final answer"

    save_trace(agent, result)
    if result.status == "punted":
        _write_waiting_entry(result)
    elif result.status != "success":
        _write_failure_entry(result)

    # Only tear down our container on success or failure. Keep it alive on punt
    # so a human can inspect / interact with it while answering.
    if EXECUTOR_TYPE == "docker" and result.status != "punted":
        cleanup_task_container(ws)

    return result


def resume(task_id: str, tools: Optional[list] = None) -> RunResult:
    """Re-run a task that was punted, using the human answer from the review queue file."""
    from tools import ALL_TOOLS

    tools = tools or ALL_TOOLS
    queue_path = REVIEW_QUEUE_ROOT / f"{task_id}.json"
    if not queue_path.exists():
        raise FileNotFoundError(f"No review-queue entry for {task_id} at {queue_path}")

    entry = json.loads(queue_path.read_text())
    if entry.get("status") != "waiting_for_human":
        raise ValueError(
            f"Entry {task_id} is status={entry.get('status')!r}, "
            "expected 'waiting_for_human'. Only punted tasks can be resumed."
        )

    human_answer = (entry.get("human_answer") or "").strip()
    if not human_answer:
        raise ValueError(
            f"No human_answer in {queue_path}. Edit the file to add your answer, then retry."
        )

    original_task = entry["task"]
    question = entry.get("question", "")
    augmented = (
        f"{original_task}\n\n"
        f"---\n"
        f"CONTEXT: In an earlier attempt you were unable to proceed and asked a human this question:\n"
        f"  {question}\n"
        f"The human answered:\n"
        f"  {human_answer}\n"
        f"Now complete the original task using this information."
    )

    new_id = f"{task_id}_resumed"
    result = run_task(augmented, tools=tools, task_id=new_id)

    if result.status == "success":
        entry["status"] = "resolved"
        entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
        entry["resumed_as"] = new_id
        queue_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        # Resume succeeded - tear down the original punt container (which was
        # kept alive by run_task's skip-cleanup-on-punt rule).
        if EXECUTOR_TYPE == "docker":
            cleanup_task_container(WORKSPACE_ROOT / task_id)

    return result
