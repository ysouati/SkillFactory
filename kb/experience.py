"""Experience index: prior solve traces + existing skills in their own collection.

Lets the factory ask "have I solved something like this before, and how?" - it
retrieves similar past tasks together with the approach (code) that solved them.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client.models import Distance, PointStruct, VectorParams

from embeddings import embed, embed_batch
from settings import (
    DENSE_VECTOR,
    EMBED_DIM,
    EXPERIENCE_COLLECTION,
    _SKILLS_JSON,
    _TRACES_DIR,
)
from stores import get_vector_client


@dataclass
class ExperienceHit:
    kind: str          # "trace" or "skill"
    ref_id: str        # task_id or skill_id
    title: str         # task text or skill name
    status: str        # trace status, or "" for skills
    approach: str      # code/approach summary (traces) or description (skills)
    score: float
    outcome: str = ""    # free-form result signal (metric summary / unmet criteria / status)
    diagnosis: str = ""  # for failed attempts: what went wrong (LLM-generated)


def ensure_experience_collection(client) -> None:
    if not client.collection_exists(EXPERIENCE_COLLECTION):
        client.create_collection(
            collection_name=EXPERIENCE_COLLECTION,
            vectors_config={DENSE_VECTOR: VectorParams(size=EMBED_DIM, distance=Distance.COSINE)},
        )


def _existing_ids(client) -> set[str]:
    ids: set[str] = set()
    offset = None
    while True:
        pts, offset = client.scroll(
            EXPERIENCE_COLLECTION, limit=256, offset=offset, with_payload=False, with_vectors=False
        )
        ids.update(str(p.id) for p in pts)
        if not pts or offset is None:
            break
    return ids


def _pid(kind: str, ref: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{kind}::{ref}"))


def _approach_from_trace(trace: dict, limit: int = 800) -> str:
    codes = [
        s["code_action"].strip()
        for s in trace.get("steps", [])
        if s.get("code_action")
    ]
    return "\n---\n".join(codes)[:limit]


def index_traces(client, traces_dir: Path = _TRACES_DIR) -> int:
    if not traces_dir.exists():
        return 0
    ensure_experience_collection(client)
    existing = _existing_ids(client)

    to_embed: list[str] = []
    pending: list[tuple[str, dict]] = []
    for f in sorted(traces_dir.glob("*.json")):
        trace = json.loads(f.read_text(encoding="utf-8"))
        run = trace.get("run", {})
        task = (run.get("task") or "").strip()
        task_id = run.get("task_id") or f.stem
        if not task:
            continue
        pid = _pid("trace", task_id)
        if pid in existing:
            continue
        pending.append((pid, {
            "kind": "trace",
            "ref_id": task_id,
            "title": task,
            "status": run.get("status", ""),
            "approach": _approach_from_trace(trace),
            "final_answer": str(run.get("final_answer", ""))[:400],
        }))
        to_embed.append(task)

    if not pending:
        return 0
    vecs = embed_batch(to_embed)
    client.upsert(
        collection_name=EXPERIENCE_COLLECTION,
        points=[
            PointStruct(id=pid, vector={DENSE_VECTOR: v}, payload=payload)
            for (pid, payload), v in zip(pending, vecs)
        ],
    )
    return len(pending)


def index_skills(client, skills_json: Path = _SKILLS_JSON) -> int:
    if not skills_json.exists():
        return 0
    ensure_experience_collection(client)
    existing = _existing_ids(client)

    skills = json.loads(skills_json.read_text(encoding="utf-8"))
    to_embed: list[str] = []
    pending: list[tuple[str, dict]] = []
    for s in skills:
        pid = _pid("skill", s["id"])
        if pid in existing:
            continue
        pending.append((pid, {
            "kind": "skill",
            "ref_id": s["id"],
            "title": s["name"],
            "status": "",
            "approach": s["description"],
            "final_answer": "",
        }))
        to_embed.append(s["description"])

    if not pending:
        return 0
    vecs = embed_batch(to_embed)
    client.upsert(
        collection_name=EXPERIENCE_COLLECTION,
        points=[
            PointStruct(id=pid, vector={DENSE_VECTOR: v}, payload=payload)
            for (pid, payload), v in zip(pending, vecs)
        ],
    )
    return len(pending)


def index_one(client, task: str, ref_id: str, status: str, approach: str,
              outcome: str = "", diagnosis: str = "") -> None:
    """Index (or overwrite) a SINGLE experience entry live - e.g. a failed attempt with its
    diagnosis. Must be called from the process that holds the Qdrant lock (the KB service), so
    the loop can add a failure mid-run and the next attempt can retrieve it via search_experience.
    """
    ensure_experience_collection(client)
    client.upsert(
        collection_name=EXPERIENCE_COLLECTION,
        points=[PointStruct(
            id=_pid("trace", ref_id),
            vector={DENSE_VECTOR: embed(task)},
            payload={"kind": "trace", "ref_id": ref_id, "title": task, "status": status,
                     "approach": approach[:1200], "final_answer": "",
                     "outcome": outcome[:400], "diagnosis": diagnosis[:1200]},
        )],
    )


def search_experience(client, query: str, k: int = 5, kind: str | None = None) -> list[ExperienceHit]:
    from qdrant_client import models

    flt = None
    if kind:
        flt = models.Filter(must=[models.FieldCondition(key="kind", match=models.MatchValue(value=kind))])
    pts = client.query_points(
        collection_name=EXPERIENCE_COLLECTION,
        query=embed(query),
        using=DENSE_VECTOR,
        query_filter=flt,
        limit=k,
        with_payload=True,
    ).points
    return [
        ExperienceHit(
            kind=p.payload["kind"],
            ref_id=p.payload["ref_id"],
            title=p.payload["title"],
            status=p.payload.get("status", ""),
            approach=p.payload.get("approach", ""),
            score=p.score,
            outcome=p.payload.get("outcome", ""),
            diagnosis=p.payload.get("diagnosis", ""),
        )
        for p in pts
    ]


if __name__ == "__main__":
    client = get_vector_client()
    nt = index_traces(client)
    ns = index_skills(client)
    total = client.count(EXPERIENCE_COLLECTION).count
    print(f"Indexed {nt} new traces, {ns} new skills. Experience collection: {total} entries.")
    client.close()
