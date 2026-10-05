"""Host-side client to the KB service (:8900), used ONLY to SOURCE verified knowledge into a
skill during optimization (grounded enrichment). The resulting skill stays fully tool-free /
portable - the KB is a build-time source, never a runtime dependency of the skill.
"""
import json
import os
from urllib.request import Request, urlopen

KB_URL = os.getenv("KB_URL", "http://localhost:8900")


def _post(path: str, payload: dict):
    """POST JSON to the KB service; return parsed JSON or None on any failure (service down etc.)."""
    try:
        req = Request(KB_URL + path, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except Exception:  # noqa: BLE001
        return None


def search_docs(query: str, doc_type: str = "attack-technique", k: int = 5) -> list:
    """Return up to k grounded passages ({citation, text}) from the KB doc store for `query`."""
    payload = {"query": query, "k": k}
    if doc_type:
        payload["doc_type"] = doc_type
    return _post("/search_docs", payload) or []


def entity_types() -> list:
    """All entity types + counts (GET /entity_types) - source-agnostic KB enumeration."""
    try:
        with urlopen(KB_URL + "/entity_types", timeout=90) as r:
            return json.loads(r.read())
    except Exception:  # noqa: BLE001
        return []


def get_entity(entity_id: str) -> dict | None:
    """Exact grounded fetch: {entity_id, entity_type, name, summary, attributes, relations_out/in}."""
    return _post("/get_entity", {"entity_id": entity_id})


def dump_type(entity_type: str, limit: int = 5000) -> list:
    """Whole-domain catalog for a type: [{entity_id, name, summary}] - used for family/prefix lookup."""
    return _post("/dump_type", {"entity_type": entity_type, "limit": limit}) or []
