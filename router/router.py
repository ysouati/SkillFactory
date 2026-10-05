from dataclasses import dataclass
from typing import Literal, Optional

from qdrant_client import QdrantClient

from embeddings import embed
from judge import JudgmentResult, judge
from vector_store import IndexedSkill, SearchHit, ensure_collection, get_store, list_all, remove_skill, search

Action = Literal["use_skill", "build"]


@dataclass
class RouterDecision:
    action: Action
    task: str
    top_score: float
    candidates: list[SearchHit]
    matched_skill_id: Optional[str] = None
    judgment: Optional[JudgmentResult] = None
    early_exit_reason: Optional[str] = None


class Router:
    def __init__(
        self,
        store: Optional[QdrantClient] = None,
        top_k: int = 3,
        min_similarity: float = 0.10,
    ):
        self.store = store or get_store()
        ensure_collection(self.store)
        self.top_k = top_k
        self.min_similarity = min_similarity

    def route(self, task: str) -> RouterDecision:
        tvec = embed(task)
        hits = search(self.store, tvec, k=self.top_k)
        top_score = hits[0].score if hits else 0.0

        if not hits:
            return RouterDecision(
                action="build",
                task=task,
                top_score=0.0,
                candidates=[],
                early_exit_reason="empty_index",
            )

        if top_score < self.min_similarity:
            return RouterDecision(
                action="build",
                task=task,
                top_score=top_score,
                candidates=hits,
                early_exit_reason=f"top_score {top_score:.3f} < {self.min_similarity}",
            )

        result = judge(task, hits)
        if result.match:
            return RouterDecision(
                action="use_skill",
                task=task,
                top_score=top_score,
                candidates=hits,
                matched_skill_id=result.match,
                judgment=result,
            )

        return RouterDecision(
            action="build",
            task=task,
            top_score=top_score,
            candidates=hits,
            judgment=result,
        )

    def list_skills(self) -> list[IndexedSkill]:
        return list_all(self.store)

    def remove_skill(self, skill_id: str) -> bool:
        return remove_skill(self.store, skill_id)

    def close(self) -> None:
        self.store.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from embeddings import embed_batch
    from skills import load_skills
    from vector_store import upsert_skill

    router = Router()
    if router.store.count("skills").count == 0:
        seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
        skills = load_skills(seed_path)
        vecs = embed_batch([s.description for s in skills])
        for skill, vec in zip(skills, vecs):
            upsert_skill(router.store, skill.id, skill.name, skill.description, vec)
        print(f"Bootstrapped index with {len(skills)} seed skills.\n")

    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "give me the main points of this whitepaper"
    decision = router.route(task)
    print(f"Task: {task!r}")
    print(f"  action={decision.action}")
    print(f"  matched={decision.matched_skill_id}")
    print(f"  top_score={decision.top_score:.3f}")
    if decision.early_exit_reason:
        print(f"  early exit: {decision.early_exit_reason}")
    if decision.judgment:
        print(f"  confidence: {decision.judgment.confidence}")
        print(f"  reason: {decision.judgment.reason}")

    router.close()
