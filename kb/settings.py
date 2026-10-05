import os
import sys
from pathlib import Path

AZURE_BASE_URL = os.getenv(
    "AZURE_BASE_URL",
    "https://YOUR_RESOURCE.openai.azure.com/openai/v1/",
)

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = int(os.getenv("EMBED_DIM", "3072"))
RERANK_MODEL = os.getenv("RERANK_MODEL", "gpt-4.1-mini")

# --- storage layout (separate from the router's qdrant_data) ---
_ROOT = Path(__file__).parent.parent
KB_ROOT = _ROOT / "kb_data"
QDRANT_PATH = KB_ROOT / "qdrant"
FACT_DB_PATH = KB_ROOT / "facts.db"

PROSE_COLLECTION = "prose"
EXPERIENCE_COLLECTION = "experience"
DENSE_VECTOR = "dense"
SPARSE_VECTOR = "bm25"

# Where prior solve traces and the skills store live (written by the factory/router)
_SKILLS_JSON = _ROOT / "skills" / "seed_skills.json"
_TRACES_DIR = _ROOT / "traces"

# --- ingestion tuning ---
CHUNK_CHARS = int(os.getenv("KB_CHUNK_CHARS", "2000"))
CHUNK_OVERLAP = int(os.getenv("KB_CHUNK_OVERLAP", "200"))
EMBED_BATCH = int(os.getenv("KB_EMBED_BATCH", "64"))

# --- retrieval defaults ---
HYBRID_PREFETCH = int(os.getenv("KB_HYBRID_PREFETCH", "40"))  # candidates per branch before fusion
RERANK_TOP_N = int(os.getenv("KB_RERANK_TOP_N", "20"))         # how many to hand the reranker
FINAL_K = int(os.getenv("KB_FINAL_K", "5"))                    # what the agent gets back


def get_api_key() -> str:
    key = os.getenv("AZURE_API_KEY")
    if not key:
        sys.exit("AZURE_API_KEY not set in environment")
    return key
