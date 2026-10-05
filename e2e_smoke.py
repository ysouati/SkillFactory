"""End-to-end smoke test: exercises the full router -> factory pipeline via the orchestrator."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from orchestrator import handle_task
from settings import REVIEW_QUEUE_ROOT, TRACE_ROOT


TEST_CASES = [
    {
        "name": "matches an existing skill",
        "task": "extract the key findings from this scientific paper",
        "expect_action": "use_skill",
        "expect_skill_id": "pdf-summarize",
    },
    {
        "name": "verifiable Python task",
        "task": (
            "Compute the SHA-256 hex digest of the ASCII string 'skill-factory' "
            "and return the hex string."
        ),
        "expect_action": "built",
    },
    {
        "name": "task requiring a shell command (ping localhost)",
        "task": (
            "Ping 127.0.0.1 exactly 2 times using the ping shell command. "
            "Return a dict with keys 'packets_received' (int) and 'command_returncode' (int)."
        ),
        "expect_action": "built",
    },
    {
        "name": "truly ambiguous task -> should punt with a question",
        "task": (
            "Deploy the app to the environment I mentioned earlier. You have no memory of "
            "which environment. Do not guess."
        ),
        "expect_action": "punted",
        "expect_question": True,  # must include a non-empty question for the human
    },
]


def main() -> None:
    print(f"{'result':<7} {'expected':<10} {'got':<10} skill/answer")
    print("-" * 90)
    passed = 0
    results = []
    for case in TEST_CASES:
        r = handle_task(case["task"])
        got = r.action
        expected = case["expect_action"]
        ok = got == expected
        if ok and expected == "use_skill" and case.get("expect_skill_id"):
            ok = r.matched_skill_id == case["expect_skill_id"]
        if ok and case.get("expect_question"):
            ok = bool(r.question) and len(r.question.strip()) > 0
        if ok:
            passed += 1
        detail = r.matched_skill_id or (
            repr(r.final_answer)[:40] if r.final_answer else (r.reason or "")[:40]
        )
        print(f"{'PASS' if ok else 'FAIL':<7} {expected:<10} {got:<10} {detail}")
        results.append((case, r))

    print("-" * 90)
    print(f"\n{passed}/{len(TEST_CASES)} passed")

    print("\n--- Detail per case ---")
    for case, r in results:
        print(f"\n[{case['name']}]")
        print(f"  task: {case['task'][:80]}")
        print(f"  action: {r.action}")
        if r.matched_skill_id:
            print(f"  matched: {r.matched_skill_id}")
            print(f"  reason:  {r.reason}")
        elif r.build_result:
            br = r.build_result
            print(f"  answer:     {br.final_answer!r}")
            print(f"  metrics:    steps={br.steps} tokens={br.input_tokens + br.output_tokens} time={br.duration_s}s")
            print(f"  trace:      traces/{br.task_id}.json")
            if r.reason:
                print(f"  reason:     {r.reason}")
            if r.question:
                print(f"  question:   {r.question}")
                print(f"  next step:  edit review_queue/{br.task_id}.json to set human_answer, then:")
                print(f"              python orchestrator.py --resume {br.task_id}")

    print("\n--- Artifact directories ---")
    traces = list(TRACE_ROOT.iterdir()) if TRACE_ROOT.exists() else []
    review = list(REVIEW_QUEUE_ROOT.iterdir()) if REVIEW_QUEUE_ROOT.exists() else []
    print(f"  traces/       {len(traces)} files")
    print(f"  review_queue/ {len(review)} files (waiting_for_human or failure entries)")


if __name__ == "__main__":
    main()
