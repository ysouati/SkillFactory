"""Three signals used to validate and refine an induced skill:

  reconstruction - does the frozen agent's trace (from the skill) resemble the original?
  outcome        - did the frozen agent actually solve the task from the skill alone?
  rubric         - is the SKILL.md well-documented and at the right abstraction level?

Each returns a score in [0, 1]; outcome and rubric also return a textual critique that the
refine step feeds back into induction.
"""
import json
import re

from llm import JUDGE_MODEL, chat, cosine, embed


def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


def reconstruction_score(orig_trace: dict, ded_trace: dict) -> float:
    """Embedding cosine between the concatenated code of the two traces."""
    def code(t):
        return "\n".join((s.get("code_action") or "") for s in t.get("steps", [])).strip()

    a, b = code(orig_trace), code(ded_trace)
    if not a or not b:
        return 0.0
    va, vb = embed([a[:8000], b[:8000]])
    return round(max(0.0, cosine(va, vb)), 3)


def outcome_score(task: str, original_final: str, ded_result: dict) -> tuple[float, str]:
    """Did the frozen deduction agent solve the task using only the skill?"""
    status = (ded_result or {}).get("status")
    if status != "success":
        return 0.0, f"deduction did not succeed (status={status}); {str((ded_result or {}).get('error'))[:200]}"
    prompt = (
        "A frozen agent solved a task using ONLY a generated skill (it never saw the original "
        "solution). Judge whether its result accomplishes the same task objective as the reference.\n\n"
        f"TASK:\n{task[:1500]}\n\n"
        f"REFERENCE RESULT (from the original successful solve):\n{str(original_final)[:800]}\n\n"
        f"DEDUCTION RESULT (from the skill):\n{str(ded_result.get('final_answer'))[:800]}\n\n"
        "Return JSON {\"score\": 0..1, \"note\": \"one sentence\"}. Score 1.0 if it clearly achieves "
        "the same objective (a correct result of the same kind), 0.0 if it does not, partial otherwise."
    )
    d = _parse_json(chat([{"role": "user", "content": prompt}], model=JUDGE_MODEL, json_mode=True, max_tokens=300))
    return round(float(d.get("score", 0.0)), 3), str(d.get("note", ""))


def rubric_score(skill_md: str) -> tuple[float, str]:
    """Documentation quality + abstraction level."""
    prompt = (
        "Rate this reusable SKILL.md on three axes, each 0..1:\n"
        "- clarity: could a competent agent follow it unambiguously?\n"
        "- generalization: right abstraction level - reusable across instances of the task family, "
        "not overfit to one instance, and not so vague it gives no guidance?\n"
        "- completeness: parameters, dependencies (tools/libs/env), and pitfalls all captured?\n\n"
        f"SKILL.md:\n{skill_md[:6000]}\n\n"
        "Return JSON {\"score\": 0..1 (overall), \"clarity\":0..1, \"generalization\":0..1, "
        "\"completeness\":0..1, \"critique\": \"specific, actionable issues to fix (1-3 sentences)\"}."
    )
    d = _parse_json(chat([{"role": "user", "content": prompt}], model=JUDGE_MODEL, json_mode=True, max_tokens=400))
    return round(float(d.get("score", 0.0)), 3), str(d.get("critique", ""))


def build_feedback(rub_critique: str, out_note: str, recon: float, outcome: float, rubric: float) -> str:
    return (
        f"Scores - reconstruction={recon}, outcome={outcome}, rubric={rubric}.\n"
        f"Outcome note: {out_note}\n"
        f"Rubric critique: {rub_critique}\n"
        "If outcome is low, the skill's procedure was not sufficient/correct for the frozen agent to "
        "reproduce the result - make the steps more precise or fix wrong instructions. If rubric is "
        "low, fix the documentation/abstraction issues above. If reconstruction is low, the procedure "
        "diverges from what actually works - align it to the proven approach."
    )
