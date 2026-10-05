"""Knowledge-base tools for the factory agent.

Thin HTTP clients over the KB service (kb/service.py). No KB package dependency
here, so they run unchanged inside the Docker sandbox. KB_URL defaults to
localhost (local executor); in Docker it is set to host.docker.internal.

Tool bodies are self-contained AND use `from urllib.request import ...` rather
than `import urllib.request` - the smolagents remote executor's validator doesn't
recognize dotted-submodule imports as binding a name.
"""
from smolagents import tool


@tool
def search_docs(query: str, doc_type: str = "") -> list:
    """Search the cybersecurity knowledge base of documents (NIST standards, MITRE
    ATT&CK technique write-ups, CWE weakness catalog) with hybrid semantic + keyword
    search and reranking. Returns passages, each with a citation to quote.

    Args:
        query: What to look for, in natural language.
        doc_type: Optional exact filter: "standard", "attack-technique", or "cwe". Empty = all.
    """
    import json
    import os
    from urllib.request import Request, urlopen

    payload = {"query": query, "k": 5}
    if doc_type:
        payload["doc_type"] = doc_type
    url = os.getenv("KB_URL", "http://localhost:8900") + "/search_docs"
    req = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=90) as r:
        return json.loads(r.read())


@tool
def kb_entity_types() -> list:
    """List the kinds of structured entities in the knowledge base (attack-technique,
    attack-tactic, cwe, ...) with counts. Call first to see what you can look up exactly.
    """
    import json
    import os
    from urllib.request import urlopen

    url = os.getenv("KB_URL", "http://localhost:8900") + "/entity_types"
    with urlopen(url, timeout=30) as r:
        return json.loads(r.read())


@tool
def kb_get(entity_id: str) -> dict:
    """Exactly fetch one structured entity by id (e.g. "T1055", "CWE-787"), with all
    attributes and relationships both directions. Use this instead of guessing facts.

    Args:
        entity_id: The exact id, e.g. "CWE-787".
    """
    import json
    import os
    from urllib.request import Request, urlopen

    url = os.getenv("KB_URL", "http://localhost:8900") + "/get_entity"
    req = Request(url, data=json.dumps({"entity_id": entity_id}).encode(),
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


@tool
def kb_find(entity_type: str = "", name_contains: str = "", attr_key: str = "", attr_value: str = "") -> list:
    """Find structured entities by exact fields (all optional, ANDed; exact except
    name_contains = case-insensitive substring).

    Args:
        entity_type: e.g. "attack-technique", "cwe". Empty = any.
        name_contains: substring of the name, e.g. "Kerbero".
        attr_key: an attribute key, e.g. "abstraction".
        attr_value: the attribute value, e.g. "Base".
    """
    import json
    import os
    from urllib.request import Request, urlopen

    payload = {}
    if entity_type:
        payload["entity_type"] = entity_type
    if name_contains:
        payload["name_contains"] = name_contains
    if attr_key:
        payload["attr_key"] = attr_key
    if attr_value:
        payload["attr_value"] = attr_value
    url = os.getenv("KB_URL", "http://localhost:8900") + "/find_entities"
    req = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


@tool
def kb_related(entity_id: str, rel_type: str = "", direction: str = "both") -> list:
    """Traverse an entity's relationships (e.g. a CWE's parents via rel_type "child-of",
    or which tactics a technique achieves via "achieves-tactic").

    Args:
        entity_id: The entity to traverse from, e.g. "CWE-121".
        rel_type: Optional exact relation filter, e.g. "child-of", "achieves-tactic". Empty = all.
        direction: "out", "in", or "both".
    """
    import json
    import os
    from urllib.request import Request, urlopen

    payload = {"entity_id": entity_id, "direction": direction}
    if rel_type:
        payload["rel_type"] = rel_type
    url = os.getenv("KB_URL", "http://localhost:8900") + "/related"
    req = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


@tool
def search_prior_solves(query: str) -> list:
    """Search prior attempts at similar tasks - INCLUDING PAST FAILURES - plus existing skills.
    Each result has: 'approach' (the code that was tried), 'status', 'outcome' (how it scored /
    which criteria were unmet), and for failures a 'diagnosis' of what went wrong. Read the
    failures so you don't repeat their mistakes, and build on the best-scoring prior approach.

    Args:
        query: A description of the current task or sub-problem.
    """
    import json
    import os
    from urllib.request import Request, urlopen

    url = os.getenv("KB_URL", "http://localhost:8900") + "/search_experience"
    req = Request(url, data=json.dumps({"query": query, "k": 5}).encode(),
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=90) as r:
        return json.loads(r.read())


KB_TOOLS = [search_docs, kb_entity_types, kb_get, kb_find, kb_related, search_prior_solves]
