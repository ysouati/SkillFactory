"""Subprocess worker: register a distilled skill into the ROUTER's skill store.

Isolated because router/ ships its own `embeddings.py` / `vector_store.py` that would
clash on sys.path with the kb/ modules. Embeds the skill's description and upserts it so
the router will thereafter route matching tasks to `use_skill`.

usage: python _router_worker.py <skill_json_path>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "router"))

from embeddings import embed  # noqa: E402
from vector_store import ensure_collection, get_store, upsert_skill  # noqa: E402

if __name__ == "__main__":
    rec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    store = get_store()
    ensure_collection(store)
    vec = embed(rec["description"])
    upsert_skill(store, rec["id"], rec["name"], rec["description"], vec)
    store.close()
    print("REGISTERED:" + rec["id"])
