"""Success gate: decide whether a solve trace met the task's success criteria.

RunResult.status == 'success' only means the agent finished cleanly, not that it solved the task
correctly. Real cyber tasks usually have no ground-truth label, so:

  - the task carries a free-text success_criteria,
  - we normalize it into a checklist,
  - an LLM judge scores each item against the result (a benchmark/objective item like
    "accuracy >= 70%" is just one checklist line read from the result).

A trace passes only if every criterion is met. Failed criteria are fed back into the next solve
attempt and annotated on the stored failed trace.
"""
import json
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from settings import AZURE_BASE_URL, get_api_key

JUDGE_MODEL = os.getenv("VERIFY_JUDGE_MODEL", "gpt-4.1-mini")


@dataclass
class CriterionResult:
    criterion: str
    passed: bool
    note: str


@dataclass
class Verdict:
    met: bool
    checklist: list = field(default_factory=list)  # list[CriterionResult]
    summary: str = ""

    def failures(self) -> list[CriterionResult]:
        return [c for c in self.checklist if not c.passed]

    def reflection(self) -> str:
        """Feedback for the next solve attempt: what was not met and why."""
        fails = self.failures()
        if not fails:
            return ""
        lines = ["The previous attempt did NOT meet these success criteria:"]
        for c in fails:
            lines.append(f"- {c.criterion} - {c.note}")
        lines.append("Address each of these specifically in the next attempt.")
        return "\n".join(lines)


def exact_match_criterion(
    artifact_path,
    pred_field: str = "final_cwe",
    gt_field: str = "gt",
    threshold: float = 60.0,
    label: str = "exact-match accuracy",
) -> "CriterionResult":
    """Objective benchmark check: recompute exact-match accuracy from the agent's per-row
    artifact (predicted vs ground-truth columns) instead of trusting the reported number.
    Returns a CriterionResult to be APPENDED to the success-criteria checklist."""
    rows = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    n = len(rows) or 1
    correct = sum(1 for r in rows if str(r.get(pred_field)) == str(r.get(gt_field)))
    acc = correct / n * 100
    return CriterionResult(
        criterion=f"Benchmark: {label} >= {threshold}% (independently computed from artifact)",
        passed=acc >= threshold,
        note=f"recomputed {acc:.1f}% ({correct}/{n}) from {Path(artifact_path).name}; threshold {threshold}%",
    )


def build_evidence(trace: dict, max_chars: int = 7000) -> str:
    """Method evidence for the judge - what the agent actually did, per step. Uses the
    model's REASONING (compact, captures intent) plus a code SIGNATURE (head+tail for long
    steps) so EVERY step is represented: process criteria (per-row, gating, GT-leakage) are
    provable without the raw code being so bulky that late steps get truncated away."""
    parts = []
    for s in trace.get("steps", []):
        code = (s.get("code_action") or "").strip()
        if not code:
            continue
        n = s.get("step_number")
        tools = [tc.get("name") for tc in (s.get("tool_calls") or [])]
        reasoning = (s.get("reasoning") or "").strip()
        sig = code if len(code) <= 500 else code[:300] + f"\n… [{len(code)} chars omitted] …\n" + code[-200:]
        block = ["# step {}{}".format(n, f"  (tools: {', '.join(tools)})" if tools else "")]
        if reasoning:
            block.append("reasoning: " + reasoning[:400])
        block.append("code: " + sig)
        parts.append("\n".join(block))
    return "\n\n".join(parts)[:max_chars]


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL)


def _chat_json(prompt: str, max_tokens: int = 1200) -> dict:
    r = _client().chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    raw = r.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


def normalize_criteria(success_criteria) -> list[str]:
    """Free-text engineer criteria -> explicit, independently-checkable checklist items.
    A list is passed through unchanged."""
    if isinstance(success_criteria, list):
        return [str(x) for x in success_criteria if str(x).strip()]
    text = str(success_criteria or "").strip()
    if not text:
        return []
    prompt = (
        "Convert the following engineer-authored success criteria for a task into a checklist of "
        "concrete, independently verifiable acceptance items. Keep every explicit requirement "
        "(including quantitative thresholds). Do not invent new requirements. "
        'Return JSON {"items": ["...", "..."]}.\n\n'
        f"Success criteria:\n{text}"
    )
    d = _chat_json(prompt, max_tokens=700)
    items = d.get("items", [])
    return [str(x) for x in items if str(x).strip()] or [text]


def verify(
    task: str,
    success_criteria,
    final_answer,
    artifacts_summary: str = "",
    benchmark_result: "CriterionResult | None" = None,
) -> Verdict:
    """Judge the produced result against each success-criteria item, then APPEND the benchmark
    criterion (if the task has one - objectively computed, not judged). `met` iff all pass."""
    items = normalize_criteria(success_criteria)
    if not items and benchmark_result is None:
        return Verdict(met=False, checklist=[], summary="no success_criteria provided")

    checklist: list[CriterionResult] = []
    summary = ""
    if items:
        numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(items))
        prompt = (
            "You are a strict acceptance judge for a security-engineering task. Decide, for EACH "
            "criterion, whether the produced result clearly satisfies it. Pass a criterion ONLY when "
            "there is explicit evidence in the result; if evidence is missing or ambiguous, fail it "
            "and say what is missing. Do not give the benefit of the doubt.\n"
            "CRITICAL: judge from the METHOD/CODE evidence, NOT from the agent's own claims about "
            "what it did - agents may falsely assert they followed a rule. For any 'do not read or "
            "use the ground-truth (GT) column when predicting' criterion: if the code reads, prints, "
            "or otherwise ACCESSES the GT/label column at any point BEFORE the predictions are "
            "finalized (e.g. a `print(... row['gt'])` or use of the GT field appears before/while "
            "predictions are built), that criterion FAILS regardless of what the agent states. Also "
            "treat statistically implausible results (e.g. precision ~1.0 on nearly every row of a "
            "hard extraction task) as a red flag of leakage and fail the no-leakage criterion.\n\n"
            f"TASK:\n{task[:2000]}\n\n"
            f"SUCCESS CRITERIA (checklist):\n{numbered}\n\n"
            f"PRODUCED RESULT (final answer):\n{str(final_answer)[:3000]}\n\n"
            + (f"METHOD / ARTIFACTS EVIDENCE (per step - reasoning + code signature):\n{artifacts_summary[:7000]}\n\n" if artifacts_summary else "")
            + 'Return JSON {"results":[{"criterion":"<verbatim item>","passed":true|false,'
            '"note":"<evidence or what is missing>"}],"summary":"one sentence overall"}.'
        )
        d = _chat_json(prompt, max_tokens=1500)
        results = d.get("results", [])
        checklist = [
            CriterionResult(
                criterion=str(r.get("criterion", items[i] if i < len(items) else "")),
                passed=bool(r.get("passed", False)),
                note=str(r.get("note", "")),
            )
            for i, r in enumerate(results)
        ] or [CriterionResult(c, False, "judge returned no result for this item") for c in items]
        summary = str(d.get("summary", ""))

    # Append the benchmark criterion (objectively computed, not judged), if the task has one.
    if benchmark_result is not None:
        checklist.append(benchmark_result)

    met = len(checklist) > 0 and all(c.passed for c in checklist)
    return Verdict(met=met, checklist=checklist, summary=summary)


def scan_violations(criteria_items: list[str], trace: dict) -> list[dict]:
    """Step-by-step audit: examine EACH step in isolation and flag any that VIOLATES a
    criterion (especially prohibitions like GT-leakage). A violation in any single step
    invalidates the whole run. Returns [{step, criterion, reason}]."""
    blocks = []
    for s in trace.get("steps", []):
        code = (s.get("code_action") or "").strip()
        if not code:
            continue
        n = s.get("step_number")
        reasoning = (s.get("reasoning") or "").strip()
        sig = code if len(code) <= 700 else code[:400] + f"\n…[{len(code)} chars]…\n" + code[-200:]
        b = f"[step {n}]"
        if reasoning:
            b += f"\n  reasoning: {reasoning[:300]}"
        b += f"\n  code: {sig}"
        blocks.append(b)
    if not blocks:
        return []
    numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(criteria_items))
    prompt = (
        "Audit this agent execution trace STEP BY STEP for rule VIOLATIONS of the criteria. "
        "Examine EACH step in isolation and decide whether that step breaks any criterion. "
        "Judge only from the code/reasoning shown, never from the agent's claims. Prohibitions "
        "matter most: for any 'do not read or use the ground-truth (GT) column when predicting' "
        "rule, a step that reads, prints, or accesses the GT/label field at any point before or "
        "while the predictions are being formed is a VIOLATION (the agent then has the answers in "
        "its context) - e.g. `print(..., row['gt'])` appearing before the predictions dict is built. "
        "IMPORTANT: reading the GT AFTER the predictions are already fixed, solely to SCORE them "
        "(compute precision/recall/F1/accuracy), is ALLOWED and is NOT a violation.\n\n"
        f"CRITERIA:\n{numbered}\n\nTRACE STEPS:\n" + "\n\n".join(blocks) + "\n\n"
        'Return JSON {"violations":[{"step":<int>,"criterion":"<the violated criterion, verbatim>",'
        '"reason":"<what in this step violates it>"}]}. Empty list if no step violates any criterion.'
    )
    d = _chat_json(prompt, max_tokens=1200)
    return d.get("violations", []) or []


def verify_trace(task, success_criteria, final_answer, trace, benchmark_result=None) -> Verdict:
    """Full verification = result-level satisfaction (verify) + step-by-step violation scan.
    A criterion FAILS if the result does not satisfy it OR any single step violates it; any
    violation makes the whole run invalid (met=False)."""
    items = normalize_criteria(success_criteria)
    evidence = build_evidence(trace)
    base = verify(task, success_criteria, final_answer, artifacts_summary=evidence,
                  benchmark_result=benchmark_result)
    violations = scan_violations(items, trace)

    checklist = list(base.checklist)
    for v in violations:
        crit = str(v.get("criterion", "")).strip()
        note = f"VIOLATED at step {v.get('step')}: {str(v.get('reason', ''))}"
        key = crit.lower()[:35]
        flipped = False
        for i, c in enumerate(checklist):
            if key and (key in c.criterion.lower() or c.criterion.lower()[:35] in crit.lower()):
                checklist[i] = CriterionResult(c.criterion, False, note)
                flipped = True
                break
        if not flipped:
            checklist.append(CriterionResult(crit or "process rule", False, note))

    met = (len(violations) == 0) and all(c.passed for c in checklist)
    summary = base.summary + (f" | STEP-SCAN: {len(violations)} violation(s)"
                              if violations else " | step-scan: clean")
    return Verdict(met=met, checklist=checklist, summary=summary)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Demo: verify the CVE->CWE trace against a sample engineer success_criteria.
    tid = sys.argv[1] if len(sys.argv) > 1 else "task_9efdb2f491c9"
    trace = json.loads((Path(__file__).parent.parent / "traces" / f"{tid}.json").read_text(encoding="utf-8"))
    run = trace["run"]
    sample_criteria = (
        "Evaluate every row of the benchmark (no batching); for each CVE first predict a CWE with "
        "a confidence, and only consult the CWE knowledge base when confidence is not high. Report "
        "both the pre-KB and post-KB exact-match accuracy over all rows, and the post-KB accuracy "
        "must be at least 60%."
    )
    print(f"Verifying trace {tid} against sample success_criteria...\n")
    evidence = build_evidence(trace)
    # This task HAS a benchmark: recompute exact-match accuracy from the per-row artifact and
    # append it as an objectively-computed criterion (not trusting the agent's reported number).
    ws_artifact = Path(__file__).parent.parent / "workspaces" / tid / "cti_rcm_kb_verify.json"
    bench = (
        exact_match_criterion(ws_artifact, "final_cwe", "gt", 60.0, "post-KB exact-match CWE accuracy")
        if ws_artifact.exists()
        else None
    )
    v = verify(run["task"], sample_criteria, run.get("final_answer"),
               artifacts_summary=evidence, benchmark_result=bench)
    for c in v.checklist:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.criterion}\n         {c.note}")
    print(f"\nMET = {v.met}   ({v.summary})")
    if not v.met:
        print("\nReflection for next attempt:\n" + v.reflection())
