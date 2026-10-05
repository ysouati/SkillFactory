import time
from functools import lru_cache

from openai import OpenAI

from settings import AZURE_BASE_URL, EMBED_MODEL, get_api_key


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=AZURE_BASE_URL)


def embed(text: str) -> list[float]:
    resp = _client().embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def embed_batch(texts: list[str], batch_size: int = 64, max_retries: int = 4) -> list[list[float]]:
    """Embed a list of texts in batches, with exponential backoff on rate limits."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                resp = _client().embeddings.create(model=EMBED_MODEL, input=chunk)
                out.extend(d.embedding for d in resp.data)
                break
            except Exception as e:
                msg = str(e)
                is_rate = "429" in msg or "rate" in msg.lower()
                if attempt == max_retries - 1 or not is_rate:
                    raise
                time.sleep(2 ** attempt + 1)
    return out
