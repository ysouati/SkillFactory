"""Induction: turn a successful trace into a reusable, generalized SKILL.md.

The induction contract sorts every concrete element of the trace into one of three
buckets:
  1. KEEP         - invariant logic / algorithm  -> generalized `procedure` steps
  2. PARAMETERIZE - values that vary per instance -> named `parameters` ({placeholders})
  3. EXTERNALIZE  - dependencies the skill needs  -> tools / libraries / env / bundled files

It also records `pitfalls` learned from the trace (errors, tricky observations, results).
Output is structured JSON, rendered to SKILL.md and mapped onto the router's Skill schema.
"""
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from llm import DISTILL_MODEL, chat

# references can be large; leave room for the JSON to finish
INDUCT_MAX_TOKENS = int(os.getenv("INDUCT_MAX_TOKENS", "8000"))

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRACES = ROOT / "traces"
OUT_DIR = ROOT / "skills" / "distilled"

CODE_CAP = 4000   # chars of code_action kept per step
OBS_CAP = 2000    # chars of observation kept per step


@dataclass
class InducedSkill:
    id: str
    name: str
    description: str
    parameters: list = field(default_factory=list)      # [{name, description, default}]
    dependencies: dict = field(default_factory=dict)     # {tools, libraries, env, other_skills} (generic)
    procedure: list = field(default_factory=list)        # [step strings]
    references: list = field(default_factory=list)       # [{filename, when_to_use, content}] bundled knowledge
    pitfalls: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# trace -> compact prompt context
# ---------------------------------------------------------------------------
def compact_trace(trace: dict) -> str:
    run = trace.get("run", {})
    out = [
        f"TASK:\n{run.get('task', '')}",
        f"\nFINAL ANSWER:\n{str(run.get('final_answer'))[:900]}",
        f"\nOUTCOME: status={run.get('status')} steps={run.get('steps')}",
        "\nEXECUTION STEPS:",
    ]
    for s in trace.get("steps", []):
        code = (s.get("code_action") or "").strip()
        if not code:
            continue
        n = s.get("step_number", "?")
        tools = [tc.get("name") for tc in (s.get("tool_calls") or [])]
        obs = str(s.get("observations") or s.get("action_output") or "")
        err = s.get("error")
        out.append(f"\n--- Step {n} | tools={tools} ---\ncode:\n{code[:CODE_CAP]}")
        if err:
            out.append(f"ERROR: {str(err)[:OBS_CAP]}")
        if obs:
            out.append(f"observation: {obs[:OBS_CAP]}")
    return "\n".join(out)


INDUCTION_SYSTEM = """You convert ONE successful agent execution trace into a single reusable, \
PORTABLE skill that ANY AI agent could follow to solve NEW instances of the same task family - on \
a completely different system, with NO access to the tools, knowledge base, services, or file \
conventions used in this trace.

Hard rules for portability:
- Do NOT mention or depend on the originating system's tools, functions, or services (never write \
"search_docs", "kb_get", "search_prior_solves", "kb_find", or similar), and do not assume specific \
infrastructure. Describe every action in general, system-agnostic terms.
- INTERNALIZE KNOWLEDGE. Whatever domain knowledge this trace obtained by calling tools or looking \
things up (mappings, definitions, reference tables, formulas, thresholds, ID lists) must be captured \
and written INTO the skill, because the target agent will NOT have those tools. The skill must CARRY \
the knowledge, not tell the agent to go fetch it.
- Package that knowledge as one or more REFERENCE DOCUMENTS (the `references` field). Each reference \
has: filename (kebab-case, ending .md), when_to_use (one line), content (self-contained markdown: the \
actual reusable knowledge - e.g. a behavior->technique mapping table, a formula with worked steps, a \
lookup list). Keep SKILL.md itself LEAN: put the bulk knowledge in references, and in the procedure \
tell the agent to consult `references/<filename>` at the step where it is needed (progressive \
disclosure - the reference is read only when required).

Abstraction and safety:
- Generalize to the TASK FAMILY, not this one instance. Reference knowledge must be GENERAL and \
transfer across instances (e.g. "HTTP/HTTPS command-and-control -> T1071.001 Web Protocols").
- NEVER include the specific answers/outputs for the particular inputs in THIS trace (no per-row \
solutions, no memorized input->output pairs). A different agent must be able to derive answers for \
UNSEEN inputs from the general knowledge you provide.
- `parameters`: values that vary per instance (paths, column names, counts, thresholds).
- `dependencies`: only GENERIC capabilities any agent needs, phrased tool-agnostically (e.g. "read a \
delimited text file", "familiarity with the MITRE ATT&CK framework"). Do NOT list the originating \
system's tool names.
- `pitfalls`: concrete lessons from THIS trace (what hurt accuracy, gotchas, checks that mattered).

Return ONLY a JSON object with keys:
  id (kebab-case slug), name (short human title),
  description (2-3 sentences: WHEN to use this skill / what task family it triggers on),
  parameters: [{name, description, default}],
  dependencies: {tools:[generic capabilities], libraries:[], env:[], other_skills:[]},
  procedure: [ ordered step strings; cite references/<filename> where the step needs that knowledge ],
  references: [ {filename, when_to_use, content} ],
  pitfalls: [ strings ]
"""


def _parse(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))


def induct(trace: dict, feedback: str = "", model: str | None = None) -> InducedSkill:
    ctx = compact_trace(trace)
    user = f"Here is the successful execution trace:\n\n{ctx}\n\nInduce the skill as specified."
    if feedback:
        user += (
            "\n\nA previous induction of this skill was validated and scored. "
            "Revise to address this feedback:\n" + feedback
        )
    raw = chat(
        [{"role": "system", "content": INDUCTION_SYSTEM}, {"role": "user", "content": user}],
        model=model or DISTILL_MODEL,
        json_mode=True,
        max_tokens=INDUCT_MAX_TOKENS,
    )
    return skill_from_dict(_parse(raw))


def skill_from_dict(d: dict) -> InducedSkill:
    """Build an InducedSkill from the induction/gradient JSON (shared by induct + the optimizer)."""
    deps = d.get("dependencies", {}) or {}
    return InducedSkill(
        id=d.get("id") or "distilled-skill",
        name=d.get("name") or "Distilled skill",
        description=(d.get("description") or "").strip(),
        parameters=d.get("parameters", []) or [],
        dependencies={
            "tools": deps.get("tools", []) or [],          # generic capabilities, NOT our tool names
            "libraries": deps.get("libraries", []) or [],
            "env": deps.get("env", []) or [],
            "other_skills": deps.get("other_skills", []) or [],
        },
        procedure=d.get("procedure", []) or [],
        references=d.get("references", []) or [],
        pitfalls=d.get("pitfalls", []) or [],
    )


# ---------------------------------------------------------------------------
# render + persist
# ---------------------------------------------------------------------------
def _safe_ref_name(name) -> str:
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", str(name or "reference"))
    return base if base.endswith(".md") else base + ".md"


def render_skill_md(sk: InducedSkill) -> str:
    # frontmatter: name + description are the fields the router matches on
    desc_line = " ".join(sk.description.split())
    L = [f"---\nname: {sk.id}\ndescription: {desc_line}\n---\n", f"# {sk.name}\n",
         "## When to use", sk.description, ""]
    if sk.parameters:
        L.append("## Parameters")
        for p in sk.parameters:
            d = f" (default: {p['default']})" if p.get("default") not in (None, "") else ""
            L.append(f"- **{p.get('name')}** - {p.get('description', '')}{d}")
        L.append("")
    if sk.references:
        L.append("## References")
        L.append("Bundled knowledge - open a file only when a step below tells you to:")
        for ref in sk.references:
            L.append(f"- `references/{_safe_ref_name(ref.get('filename'))}` - {ref.get('when_to_use', '')}")
        L.append("")
    dep = sk.dependencies
    reqs = list(dep.get("tools", []))                       # generic capabilities
    if dep.get("libraries"):
        reqs.append("libraries: " + ", ".join(dep["libraries"]))
    if dep.get("env"):
        reqs.append("env: " + ", ".join(dep["env"]))
    if reqs:
        L.append("## Requirements")
        for r in reqs:
            L.append(f"- {r}")
        for os_ in dep.get("other_skills", []):
            L.append(f"- Composes with: [[{os_}]]")
        L.append("")
    L.append("## Procedure")
    for i, step in enumerate(sk.procedure, 1):
        L.append(f"{i}. {step}")
    L.append("")
    if sk.pitfalls:
        L.append("## Pitfalls")
        for pf in sk.pitfalls:
            L.append(f"- {pf}")
        L.append("")
    return "\n".join(L)


def write_skill_package(sk: InducedSkill, md: str, dest: Path) -> Path:
    """Write a skill package: dest/SKILL.md + dest/references/*.md."""
    (dest / "references").mkdir(parents=True, exist_ok=True)
    md_path = dest / "SKILL.md"
    md_path.write_text(md, encoding="utf-8")
    for ref in sk.references:
        (dest / "references" / _safe_ref_name(ref.get("filename"))).write_text(
            str(ref.get("content", "")), encoding="utf-8")
    return md_path


def save_skill(sk: InducedSkill, md: str) -> tuple[Path, Path]:
    """Persist the skill as its own directory under skills/distilled/<id>/ and write the
    router index record (skill.json). Returns (SKILL.md path, skill.json path)."""
    skill_dir = OUT_DIR / sk.id
    md_path = write_skill_package(sk, md, skill_dir)
    json_path = skill_dir / "skill.json"
    # Router's Skill schema (id/name/description are load-bearing); references indexed by name only.
    skill_record = {
        "id": sk.id,
        "name": sk.name,
        "description": sk.description,
        "procedure": "\n".join(f"{i}. {s}" for i, s in enumerate(sk.procedure, 1)),
        "requirements": sk.dependencies.get("tools", []),
        "references": [{"filename": _safe_ref_name(r.get("filename")),
                        "when_to_use": r.get("when_to_use", "")} for r in sk.references],
        "examples": [],
        "corner_cases": sk.pitfalls,
        "parameters": sk.parameters,
        "dependencies": sk.dependencies,
    }
    json_path.write_text(json.dumps(skill_record, indent=2), encoding="utf-8")
    return md_path, json_path


def load_trace(task_id: str) -> dict:
    p = TRACES / f"{task_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"No trace at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        sys.exit("usage: python induct.py <task_id>")
    tid = sys.argv[1]
    trace = load_trace(tid)
    print(f"Inducing skill from trace {tid} (model={DISTILL_MODEL})...\n", flush=True)
    skill = induct(trace)
    md = render_skill_md(skill)
    md_path, json_path = save_skill(skill, md)
    print(md)
    print(f"\nsaved -> {md_path}\n         {json_path}")
