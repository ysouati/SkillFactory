from typing import Optional

from pydantic import BaseModel, Field

from config import JUDGE_MODEL, get_client
from vector_store import SearchHit


class JudgmentResult(BaseModel):
    match: Optional[str] = Field(
        description="The skill_id of the applicable candidate, or null if none apply."
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="0.0 (unsure) to 1.0 (certain)."
    )
    reason: str = Field(description="Brief justification for the decision.")


SYSTEM_PROMPT = """You are a strict skill-matcher for a task-execution system.

Given a user task and a list of candidate skills retrieved by semantic similarity,
decide whether ANY candidate ACTUALLY applies to this task.

Be strict:
- If the task requires functionality the candidate does not cover, return no match.
- Superficial keyword overlap is not enough - the candidate must actually solve the task.
- If multiple candidates apply, pick the best fit.
- If uncertain, prefer no match (null) - the system can build a new skill.

Return a structured JSON object with:
- match: the skill_id that applies, or null
- confidence: 0.0 to 1.0
- reason: one sentence explaining the decision
"""


def judge(task: str, candidates: list[SearchHit]) -> JudgmentResult:
    if not candidates:
        return JudgmentResult(match=None, confidence=1.0, reason="No candidates provided.")

    candidate_lines = [
        f"{i + 1}. [{c.skill_id}] {c.name}\n   {c.description}"
        for i, c in enumerate(candidates)
    ]
    user_prompt = "Task:\n" + task + "\n\nCandidate skills:\n" + "\n\n".join(candidate_lines)

    resp = get_client().beta.chat.completions.parse(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=JudgmentResult,
        temperature=0,
    )
    return resp.choices[0].message.parsed


if __name__ == "__main__":
    from pathlib import Path
    from embeddings import embed, embed_batch
    from skills import load_skills
    from vector_store import ensure_collection, get_store, search, upsert_skill

    seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
    skills = load_skills(seed_path)

    client = get_store()
    ensure_collection(client)
    if client.count("skills").count < len(skills):
        vecs = embed_batch([s.description for s in skills])
        for skill, vec in zip(skills, vecs):
            upsert_skill(client, skill.id, skill.name, skill.description, vec)

    queries = [
        "summarize this research paper for me",
        "my customer CSV has inconsistent date formats",
        "build a 5-year revenue forecast in Excel",
        "extract action items from this transcript",
        "translate this document from English to French",
        "edit an image to remove the background",
    ]

    print(f"Testing judgment via {JUDGE_MODEL}\n" + "=" * 60)
    for q in queries:
        qv = embed(q)
        hits = search(client, qv, k=3)
        result = judge(q, hits)
        print(f"\nQuery: {q!r}")
        print(f"  Top hits: {[(h.skill_id, round(h.score, 3)) for h in hits]}")
        print(f"  match={result.match!r}  conf={result.confidence}")
        print(f"  reason: {result.reason}")

    client.close()
