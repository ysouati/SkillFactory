import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    """A reusable skill in the store.

    For the router, only `id`, `name`, and `description` are load-bearing -
    the rest is populated when the factory creates or updates a skill.
    """

    id: str
    name: str
    description: str
    procedure: str = ""
    tools: list[str] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)
    corner_cases: list[str] = field(default_factory=list)


def load_skills(path: str | Path) -> list[Skill]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Skill(**s) for s in raw]


if __name__ == "__main__":
    seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
    skills = load_skills(seed_path)
    print(f"Loaded {len(skills)} skills from {seed_path}")
    for s in skills:
        print(f"  [{s.id}] {s.name}")
        print(f"      {s.description}")
