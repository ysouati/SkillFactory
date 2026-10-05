"""Local HTTP service exposing the KB as retrieval tools.

The factory agent (in-process or in a Docker container) calls these endpoints;
the KB's data, Azure embeddings, and BM25 model all stay here on the host.
Single-threaded on purpose: one agent, sequential calls, no SQLite/Qdrant
concurrency to worry about.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from experience import index_one, search_experience
from fact_store import dump_type, entity_types, find_entities, get_entity, related
from retrieve import search as prose_search
from stores import get_fact_db, get_vector_client

VC = get_vector_client()
DB = get_fact_db()


def _prose(query, k=5, doc_type=None):
    hits = prose_search(VC, query, k=k, doc_type=doc_type or None)
    return [
        {"citation": h.citation, "text": h.text, "source_id": h.source_id,
         "source_url": h.source_url, "doc_type": h.doc_type, "score": round(h.score, 4)}
        for h in hits
    ]


def _experience(query, k=5, kind=None):
    hits = search_experience(VC, query, k=k, kind=kind or None)
    return [
        {"kind": h.kind, "ref_id": h.ref_id, "title": h.title, "status": h.status,
         "approach": h.approach, "score": round(h.score, 4),
         "outcome": h.outcome, "diagnosis": h.diagnosis}
        for h in hits
    ]


def _add_experience(task, ref_id, status, approach="", outcome="", diagnosis=""):
    """Index one failed attempt (with its diagnosis) into the experience store, live."""
    index_one(VC, task=task, ref_id=ref_id, status=status, approach=approach,
              outcome=outcome, diagnosis=diagnosis)
    return {"ok": True, "ref_id": ref_id}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/health":
                return self._send({"ok": True})
            if path == "/entity_types":
                return self._send(entity_types(DB))
            self._send({"error": "not found"}, 404)
        except Exception as e:
            self._send({"error": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            if path == "/search_docs":
                return self._send(_prose(**body))
            if path == "/get_entity":
                return self._send(get_entity(DB, body["entity_id"]))
            if path == "/find_entities":
                return self._send(find_entities(DB, **body))
            if path == "/dump_type":
                return self._send(dump_type(DB, **body))
            if path == "/related":
                return self._send(related(DB, **body))
            if path == "/search_experience":
                return self._send(_experience(**body))
            if path == "/add_experience":
                return self._send(_add_experience(**body))
            self._send({"error": "not found"}, 404)
        except Exception as e:
            self._send({"error": f"{type(e).__name__}: {e}"}, 500)


if __name__ == "__main__":
    port = int(os.getenv("KB_PORT", "8900"))
    print(f"KB service listening on 0.0.0.0:{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
