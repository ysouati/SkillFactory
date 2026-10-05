import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from smolagents import CodeAgent

from settings import TRACE_ROOT


_STEP_ATTRS = (
    "step_number",
    "code_action",
    "observations",
    "error",
    "input_token_count",
    "output_token_count",
    "duration",
    "action_output",
)


def _extract_reasoning(model_output: Any) -> str | None:
    """The model's stated reasoning for a step: its raw output with fenced code blocks
    stripped out. Much more compact than the code, and captures intent (e.g. "print the
    GT to compare") that pure code truncation can lose."""
    if not model_output:
        return None
    text = re.sub(r"```.*?```", " ", str(model_output), flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600] or None


def _stringify_error(e: Any) -> Any:
    if isinstance(e, BaseException):
        return f"{type(e).__name__}: {e}"
    return e


def serialize_step(step: Any) -> dict[str, Any]:
    d: dict[str, Any] = {"type": type(step).__name__}
    for attr in _STEP_ATTRS:
        val = getattr(step, attr, None)
        if val is None:
            continue
        d[attr] = _stringify_error(val)
    reasoning = _extract_reasoning(getattr(step, "model_output", None))
    if reasoning:
        d["reasoning"] = reasoning
    tool_calls = getattr(step, "tool_calls", None) or []
    if tool_calls:
        d["tool_calls"] = [
            {
                "name": getattr(tc, "name", None),
                "arguments": getattr(tc, "arguments", None),
                "id": getattr(tc, "id", None),
            }
            for tc in tool_calls
        ]
    return d


def save_trace(agent: CodeAgent, run_result: Any) -> Path:
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)
    result_dict = asdict(run_result) if hasattr(run_result, "__dataclass_fields__") else dict(run_result)
    payload = {
        "run": result_dict,
        "steps": [serialize_step(s) for s in agent.memory.steps],
    }
    trace_path = TRACE_ROOT / f"{result_dict['task_id']}.json"
    trace_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return trace_path
