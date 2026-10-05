import os
import sys
from pathlib import Path
from textwrap import dedent

AZURE_BASE_URL = os.getenv(
    "AZURE_BASE_URL",
    "https://YOUR_RESOURCE.openai.azure.com/openai/v1/",
)

FACTORY_MODEL = os.getenv("FACTORY_MODEL", "gpt-5.4")
DISTILL_MODEL = os.getenv("DISTILL_MODEL", "gpt-5.4")

MAX_STEPS = int(os.getenv("FACTORY_MAX_STEPS", "10"))
WALL_CLOCK_TIMEOUT_S = int(os.getenv("FACTORY_TIMEOUT_S", "300"))
MAX_TOOL_CALLS = int(os.getenv("FACTORY_MAX_TOOL_CALLS", "30"))
SHELL_TIMEOUT_S = int(os.getenv("SHELL_TIMEOUT_S", "60"))
# per-request LLM timeout + retries (the SDK default is 600s)
FACTORY_LLM_TIMEOUT = float(os.getenv("FACTORY_LLM_TIMEOUT", "240"))
FACTORY_LLM_RETRIES = int(os.getenv("FACTORY_LLM_RETRIES", "3"))

# optional non-Azure OpenAI-compatible endpoint (e.g. a local server); empty = use Azure
FACTORY_LLM_BASE_URL = os.getenv("FACTORY_LLM_BASE_URL", "")
FACTORY_LLM_API_KEY = os.getenv("FACTORY_LLM_API_KEY", "")

EXECUTOR_TYPE = os.getenv("EXECUTOR_TYPE", "local").lower()

_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = _ROOT / "workspaces"
TRACE_ROOT = _ROOT / "traces"
REVIEW_QUEUE_ROOT = _ROOT / "review_queue"

DOCKER_IMAGE_NAME = os.getenv("DOCKER_IMAGE_NAME", "skill-factory-agent")

DOCKERFILE_CONTENT = dedent(
    """\
    FROM python:3.12-bullseye

    RUN apt-get update && apt-get install -y --no-install-recommends \\
        curl \\
        git \\
        jq \\
        && rm -rf /var/lib/apt/lists/*

    RUN pip install --no-cache-dir \\
        jupyter_kernel_gateway \\
        jupyter_client \\
        ipykernel \\
        pandas \\
        numpy

    WORKDIR /workspace

    EXPOSE 8888
    CMD ["jupyter", "kernelgateway", "--KernelGatewayApp.ip=0.0.0.0", "--KernelGatewayApp.port=8888"]
    """
)


def get_api_key() -> str:
    key = os.getenv("AZURE_API_KEY")
    if not key:
        sys.exit("AZURE_API_KEY not set in environment")
    return key
