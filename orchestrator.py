"""Top-level orchestrator: routes a task to an existing skill, or invokes the factory."""
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).parent
sys.path.append(str(_ROOT / "router"))
sys.path.append(str(_ROOT / "factory"))

from router import Router  # noqa: E402
from build_skill import build_skill  # noqa: E402
from runner import RunResult, resume  # noqa: E402


@dataclass
class OrchestrationResult:
    action: Literal["use_skill", "built", "punted", "failed"]
    task: str
    matched_skill_id: Optional[str] = None
    build_result: Optional[RunResult] = None
    final_answer: Any = None
    reason: Optional[str] = None
    question: Optional[str] = None


def handle_task(task: str, router: Optional[Router] = None) -> OrchestrationResult:
    """Route a task, then dispatch to the factory if no skill matches."""
    router = router or Router()
    decision = router.route(task)

    if decision.action == "use_skill":
        return OrchestrationResult(
            action="use_skill",
            task=task,
            matched_skill_id=decision.matched_skill_id,
            reason=decision.judgment.reason if decision.judgment else None,
        )

    build = build_skill(task)
    if build.status == "success":
        return OrchestrationResult(
            action="built",
            task=task,
            build_result=build,
            final_answer=build.final_answer,
        )
    if build.status == "punted":
        return OrchestrationResult(
            action="punted",
            task=task,
            build_result=build,
            reason=build.punt_reason,
            question=build.punt_question,
        )
    return OrchestrationResult(
        action="failed",
        task=task,
        build_result=build,
        reason=build.error,
    )


def _print_build_result(br: RunResult, reason: Optional[str] = None, question: Optional[str] = None) -> None:
    print(f"Task ID: {br.task_id}")
    print(f"Final answer: {br.final_answer!r}")
    print(f"Metrics: {br.steps} steps, {br.input_tokens + br.output_tokens} tokens, {br.duration_s}s")
    print(f"Trace: traces/{br.task_id}.json")
    if br.workspace:
        ws = Path(br.workspace)
        artifacts = [p.name for p in ws.iterdir()] if ws.exists() else []
        print(f"Workspace: {br.workspace}")
        if artifacts:
            print(f"Artifacts: {artifacts}")
    if question:
        print(f"Question for human: {question}")
        print(f"To answer: edit review_queue/{br.task_id}.json (set 'human_answer'), then run:")
        print(f"  python orchestrator.py --resume {br.task_id}")
    if reason:
        print(f"Reason: {reason}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("task", nargs="*", default=[], help="Task description")
    group.add_argument("--resume", metavar="TASK_ID", help="Resume a punted task after editing its review_queue entry")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")

    if args.resume:
        print(f"Resuming task: {args.resume}")
        try:
            br = resume(args.resume)
        except (FileNotFoundError, ValueError) as e:
            sys.exit(f"Cannot resume: {e}")
        print(f"Status: {br.status}")
        _print_build_result(br, reason=br.punt_reason, question=br.punt_question)
    else:
        task = " ".join(args.task)
        if not task:
            sys.exit("Provide a task or --resume <task_id>")
        result = handle_task(task)
        print(f"Task: {task!r}")
        print(f"Action: {result.action}")
        if result.matched_skill_id:
            print(f"Matched skill: {result.matched_skill_id}")
            print(f"Reason: {result.reason}")
        elif result.build_result:
            _print_build_result(result.build_result, reason=result.reason, question=result.question)
