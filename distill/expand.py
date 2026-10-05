"""Knowledge expansion (opt-in via DISTILL_EXPAND_KNOWLEDGE=1).

By default distillation keeps only the knowledge the trace used. With the flag on, after induction
we take every KB entity the skill references and pull its related cluster (the same-parent family
and same-type neighbors) from the KB, then fold that into the skill's references. The skill stays
tool-free; the KB is only a build-time source. Requires the KB service to be running.

Detection is KB-driven: entity IDs are matched against the KB's own id set, so it is not tied to any
one ID scheme. The expanded skill id is suffixed `-expanded` so it coexists with the original.
"""
import os
import re

from induct import render_skill_md
from kb_client import dump_type, entity_types, get_entity
from optimize import _refs_text, apply_gradient

# Maximal id-shaped token (alnum runs joined by . _ - /), no trailing separator. Broad on purpose:
# every candidate is validated against the KB's real id set, so shape only has to be permissive.
CAND = re.compile(r"[A-Za-z0-9]+(?:[._/\-][A-Za-z0-9]+)*")
MAX_CLUSTER = int(os.getenv("EXPAND_MAX_CLUSTER", "150"))     # bound the bundle so the skill can't balloon
MAX_INDEX = int(os.getenv("EXPAND_MAX_INDEX", "20000"))       # safety cap on KB id enumeration
OBS_CAP = 8000                                                # per-step observation chars scanned for ids


def _kb_index() -> dict:
    """id -> {name, summary, type} for EVERY entity in the KB (all types). This is what makes
    detection KB-driven rather than tied to any ID pattern. One pass per expansion."""
    idx: dict[str, dict] = {}
    for t in entity_types() or []:
        et = t.get("entity_type")
        if not et:
            continue
        for e in dump_type(et):
            idx[e.get("entity_id")] = {"name": e.get("name", ""),
                                       "summary": e.get("summary", ""), "type": et}
            if len(idx) >= MAX_INDEX:
                return idx
    return idx


def _used_ids(skill, trace, index: dict) -> list:
    """Every KB entity id that appears in the skill (references + procedure) or the trace (what the
    tools retrieved). KB-driven: candidate tokens intersected with the KB's real id set."""
    parts = [str(r.get("content", "")) for r in skill.references] + list(skill.procedure)
    for s in trace.get("steps", []):
        parts.append(str(s.get("observations") or s.get("action_output") or "")[:OBS_CAP])
    cands = set(CAND.findall(" ".join(parts)))
    return sorted(cands & set(index))                        # keep only tokens that are REAL KB ids


def _expand(used_ids: list, index: dict) -> tuple[str, str, int]:
    """Grounded bundle for the related cluster of every used id. Returns (bundle_text, types, n)."""
    by_type: dict[str, list] = {}                            # type -> ids (derived from the index; no extra calls)
    for eid, info in index.items():
        by_type.setdefault(info["type"], []).append(eid)

    cluster: dict[str, str] = {}                             # id -> "id - name: summary"

    def add(eid):
        info = index.get(eid)
        if info and eid not in cluster and len(cluster) < MAX_CLUSTER:
            name = " ".join(str(info["name"] or "").split())          # collapse any newlines -> one clean
            summ = " ".join(str(info["summary"] or "").split())[:200]  # line per entity in the bundle
            cluster[eid] = f"{eid} - {name}: {summ}"

    for uid in used_ids:
        utype = index[uid]["type"]
        add(uid)
        pfx = uid.split(".")[0]                              # same-parent family (bonus for hierarchical ids;
        for cid in by_type.get(utype, []):                  # graceful no-op when ids aren't hierarchical)
            if cid == pfx or cid.startswith(pfx + "."):
                add(cid)
        e = get_entity(uid)                                  # relations (dump_type doesn't include them)
        if e:
            for r in (e.get("relations_out") or []) + (e.get("relations_in") or []):
                rid = r.get("id", "")
                if rid in index and index[rid]["type"] == utype:   # SAME-TYPE neighbors only: keeps the
                    add(rid)                                        # family, drops cross-type "uses" floods
    types = ",".join(sorted({index[u]["type"] for u in used_ids}))
    return "\n".join(sorted(cluster.values())), types, len(cluster)


def expand_knowledge(skill, trace):
    """Expand the skill's used KB knowledge to its full related cluster and LLM-weave the grounded
    knowledge into the references. Returns the (new, `-expanded`) skill; a no-op passthrough if the
    KB is unreachable or the skill/trace references no KB entities."""
    index = _kb_index()
    if not index:
        print("  [expand] KB unreachable/empty; skipping expansion.", flush=True)
        return skill
    used = _used_ids(skill, trace, index)
    if not used:
        print("  [expand] no KB entity IDs found in skill/trace; skipping (nothing to relate).", flush=True)
        return skill
    bundle, types, n = _expand(used, index)
    print(f"  [expand] {len(used)} used KB IDs ({types}) -> {n} related entities; weaving into references...",
          flush=True)
    diagnosis = (
        "Expand the bundled knowledge so that for EVERY item the skill already references, the COMPLETE "
        "related family is covered: the parent item, ALL sibling sub-items, and directly related items - "
        "not only the specific ones used so far. Add these as general, portable domain knowledge; do not "
        "narrow coverage to the observed cases."
    )
    md = render_skill_md(skill)
    new_skill = apply_gradient(diagnosis, bundle, md, _refs_text(skill))   # reuse the portable LLM-weave
    suffix = os.getenv("EXPAND_SUFFIX", "-expanded")
    if not new_skill.id.endswith(suffix):
        new_skill.id += suffix                                             # coexist with the used-only skill
    return new_skill
