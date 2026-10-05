"""Azure OpenAI helpers for the distillation module.

Self-contained so it does not clash with the factory/kb/router settings modules on sys.path.
"""
import math
import os
import time
from functools import lru_cache

from openai import OpenAI

AZURE_BASE_URL = os.getenv("AZURE_BASE_URL", "https://YOUR_RESOURCE.openai.azure.com/openai/v1/")
DISTILL_MODEL = os.getenv("DISTILL_MODEL", "gpt-5.4")
JUDGE_MODEL = os.getenv("DISTILL_JUDGE_MODEL", "gpt-4.1-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    key = os.getenv("AZURE_API_KEY")
    if not key:
        raise SystemExit("AZURE_API_KEY not set in environment")
    return OpenAI(api_key=key, base_url=AZURE_BASE_URL,
                  timeout=float(os.getenv("DISTILL_LLM_TIMEOUT", "240")))


def chat(messages, model=None, temperature=0, max_tokens=1800, json_mode=False, max_retries=4) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    last = None
    for attempt in range(max_retries):
        try:
            r = _client().chat.completions.create(
                model=model or DISTILL_MODEL,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                **kwargs,
            )
            return r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt + 1)
    raise last


def embed(texts):
    single = isinstance(texts, str)
    batch = [texts] if single else list(texts)
    r = _client().embeddings.create(model=EMBED_MODEL, input=batch)
    vecs = [d.embedding for d in r.data]
    return vecs[0] if single else vecs


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
