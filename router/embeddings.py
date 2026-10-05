from functools import lru_cache
from openai import OpenAI
from config import get_client, EMBED_MODEL


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return get_client()


def embed(text: str) -> list[float]:
    resp = _client().embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def embed_batch(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        resp = _client().embeddings.create(model=EMBED_MODEL, input=chunk)
        out.extend(d.embedding for d in resp.data)
    return out


if __name__ == "__main__":
    import math
    from pathlib import Path
    from skills import load_skills

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb)

    seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
    skills = load_skills(seed_path)

    print(f"Embedding {len(skills)} skill descriptions in one batch...")
    skill_vecs = embed_batch([s.description for s in skills])
    print(f"  OK. Got {len(skill_vecs)} vectors, dim={len(skill_vecs[0])}")

    tasks = [
        "summarize this research paper for me",
        "my customer CSV has inconsistent date formats and extra whitespace",
        "build a 5-year revenue forecast in Excel with sensitivity analysis",
        "extract action items from this Zoom meeting transcript",
        "translate this document from English to French",
    ]

    print("\nSanity check: cosine similarity task -> each skill")
    print(f"{'task':<60}  " + "  ".join(f"{s.id[:12]:>12}" for s in skills))
    print("-" * (60 + 4 + 14 * len(skills)))
    for task in tasks:
        tvec = embed(task)
        sims = [cosine(tvec, sv) for sv in skill_vecs]
        best = sims.index(max(sims))
        row = "  ".join(
            (f"[{sim:.3f}]" if i == best else f" {sim:.3f} ")
            for i, sim in enumerate(sims)
        )
        print(f"{task[:60]:<60}  {row}")
