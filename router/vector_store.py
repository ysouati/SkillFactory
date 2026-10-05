from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_DNS, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import EMBED_DIM

COLLECTION = "skills"
DEFAULT_STORAGE = Path(__file__).parent.parent / "qdrant_data"


@dataclass
class SearchHit:
    skill_id: str
    name: str
    description: str
    score: float


@dataclass
class IndexedSkill:
    skill_id: str
    name: str
    description: str


def get_store(path: str | Path = DEFAULT_STORAGE) -> QdrantClient:
    return QdrantClient(path=str(path))


def ensure_collection(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )


def _point_id(skill_id: str) -> str:
    return str(uuid5(NAMESPACE_DNS, skill_id))


def upsert_skill(
    client: QdrantClient,
    skill_id: str,
    name: str,
    description: str,
    vector: list[float],
) -> None:
    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=_point_id(skill_id),
                vector=vector,
                payload={
                    "skill_id": skill_id,
                    "name": name,
                    "description": description,
                },
            )
        ],
    )


def search(client: QdrantClient, vector: list[float], k: int = 5) -> list[SearchHit]:
    results = client.query_points(
        collection_name=COLLECTION, query=vector, limit=k
    ).points
    return [
        SearchHit(
            skill_id=r.payload["skill_id"],
            name=r.payload["name"],
            description=r.payload["description"],
            score=r.score,
        )
        for r in results
    ]


def remove_skill(client: QdrantClient, skill_id: str) -> bool:
    """Delete a skill by skill_id. Returns True if the point existed and was removed."""
    result = client.delete(
        collection_name=COLLECTION,
        points_selector=[_point_id(skill_id)],
    )
    return result.status.value in {"completed", "acknowledged"} if result else False


def list_all(client: QdrantClient, limit: int = 1000) -> list[IndexedSkill]:
    points, _ = client.scroll(
        collection_name=COLLECTION,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [
        IndexedSkill(
            skill_id=p.payload["skill_id"],
            name=p.payload["name"],
            description=p.payload["description"],
        )
        for p in points
    ]


if __name__ == "__main__":
    from embeddings import embed, embed_batch
    from skills import load_skills

    seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
    skills = load_skills(seed_path)

    client = get_store()
    ensure_collection(client)

    print(f"Embedding + upserting {len(skills)} skills...")
    vecs = embed_batch([s.description for s in skills])
    for skill, vec in zip(skills, vecs):
        upsert_skill(client, skill.id, skill.name, skill.description, vec)
    print(f"  OK. Collection '{COLLECTION}' contains {client.count(COLLECTION).count} points")

    queries = [
        "summarize this research paper for me",
        "my customer CSV has inconsistent date formats",
        "build a 5-year revenue forecast in Excel",
        "extract action items from this transcript",
        "translate this document from English to French",
    ]

    print("\nTop-3 hits per query:")
    for q in queries:
        qv = embed(q)
        hits = search(client, qv, k=3)
        print(f"\n  query: {q!r}")
        for h in hits:
            print(f"    {h.score:.3f}  {h.skill_id:<28}  {h.name}")

    client.close()
