import os
import sys
from openai import OpenAI

AZURE_BASE_URL = os.getenv(
    "AZURE_BASE_URL",
    "https://YOUR_RESOURCE.openai.azure.com/openai/v1/",
)

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = int(os.getenv("EMBED_DIM", "3072"))

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4.1-mini")


def get_client() -> OpenAI:
    key = os.getenv("AZURE_API_KEY")
    if not key:
        sys.exit("AZURE_API_KEY not set in environment")
    return OpenAI(api_key=key, base_url=AZURE_BASE_URL)
