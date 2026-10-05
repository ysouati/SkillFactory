from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from uuid import uuid4

from smolagents import CodeAgent, OpenAIServerModel

from settings import (
    AZURE_BASE_URL,
    DOCKER_IMAGE_NAME,
    DOCKERFILE_CONTENT,
    EXECUTOR_TYPE,
    FACTORY_LLM_API_KEY,
    FACTORY_LLM_BASE_URL,
    FACTORY_LLM_RETRIES,
    FACTORY_LLM_TIMEOUT,
    FACTORY_MODEL,
    MAX_STEPS,
    WORKSPACE_ROOT,
    get_api_key,
)


def new_task_id() -> str:
    return "task_" + uuid4().hex[:12]


def make_workspace(task_id: str) -> Path:
    ws = WORKSPACE_ROOT / task_id
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@contextmanager
def in_workspace(ws: Path):
    import os

    old = os.getcwd()
    os.chdir(ws)
    try:
        yield ws
    finally:
        os.chdir(old)


def build_model() -> OpenAIServerModel:
    # use FACTORY_LLM_BASE_URL/API_KEY if set, otherwise Azure
    base = FACTORY_LLM_BASE_URL or AZURE_BASE_URL
    key = FACTORY_LLM_API_KEY or get_api_key()
    return OpenAIServerModel(
        model_id=FACTORY_MODEL,
        api_base=base,
        api_key=key,
        client_kwargs={"timeout": FACTORY_LLM_TIMEOUT, "max_retries": FACTORY_LLM_RETRIES},
    )


def _container_name(workspace: Path) -> str:
    """Docker container name derived from the workspace (task_id).

    Docker names must match [a-zA-Z0-9][a-zA-Z0-9_.-]*. Our task_ids do.
    """
    return f"skill-factory-{workspace.name}"


def _free_port() -> int:
    """Return an OS-assigned free TCP port. Race-safe enough for our sequential use."""
    import socket

    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def cleanup_task_container(workspace: Path) -> bool:
    """Force-remove the container specifically bound to this task (by unique name).

    Called before every Docker run (in build_agent) so a re-run of the same task_id
    doesn't collide with its previous incarnation, and after every SUCCESSFUL or
    FAILED run in the runner. NOT called after punts - punted containers stay alive
    so a human can still poke at them (docker exec) while answering.
    """
    try:
        import docker

        client = docker.from_env()
        try:
            c = client.containers.get(_container_name(workspace))
            c.remove(force=True)
            return True
        except docker.errors.NotFound:
            return False
    except Exception:
        return False


def cleanup_all_containers() -> int:
    """Force-remove ALL containers built from our image. Manual sweep (not auto).

    Use this to clear out accumulated punt-container debt when you no longer intend
    to resume them.
    """
    try:
        import docker

        client = docker.from_env()
        removed = 0
        for c in client.containers.list(all=True, filters={"ancestor": DOCKER_IMAGE_NAME}):
            try:
                c.remove(force=True)
                removed += 1
            except Exception:
                pass
        return removed
    except Exception:
        return 0


def _docker_executor_kwargs(workspace: Path) -> dict:
    """Return executor_kwargs for smolagents DockerExecutor with:
    - workspace mounted at /workspace
    - unique container name per task (avoids Docker name collision)
    - OS-assigned random host port (avoids port 8888 collision when multiple
      tasks are in flight, e.g. one punted + another running)
    - AZURE_API_KEY + AZURE_BASE_URL passed through so the agent inside the
      container can make its own LLM calls if a task requires that
    """
    import os

    container_env = {
        "AZURE_BASE_URL": AZURE_BASE_URL,
        "AZURE_API_KEY": get_api_key(),
        # in-container agents reach the host KB service via host.docker.internal
        "KB_URL": os.environ.get("KB_URL_DOCKER", "http://host.docker.internal:8900"),
    }

    return {
        "image_name": DOCKER_IMAGE_NAME,
        "build_new_image": False,
        "dockerfile_content": DOCKERFILE_CONTENT,
        "port": _free_port(),
        "container_run_kwargs": {
            "volumes": {
                str(workspace.resolve()): {"bind": "/workspace", "mode": "rw"},
            },
            "working_dir": "/workspace",
            "name": _container_name(workspace),
            "environment": container_env,
        },
    }


def build_agent(
    tools: list,
    workspace: Optional[Path] = None,
    authorized_imports: Optional[list[str]] = None,
) -> CodeAgent:
    # local: import allowlist (supports "*"); docker: pip-install list ("*" invalid there)
    if EXECUTOR_TYPE == "docker":
        imports = authorized_imports if authorized_imports is not None else []
    else:
        imports = authorized_imports if authorized_imports is not None else ["*"]

    kwargs = {}
    if EXECUTOR_TYPE == "docker":
        if workspace is None:
            raise ValueError("Docker executor requires a workspace path to mount")
        cleanup_task_container(workspace)
        kwargs["executor_type"] = "docker"
        kwargs["executor_kwargs"] = _docker_executor_kwargs(workspace)
    return CodeAgent(
        tools=tools,
        model=build_model(),
        max_steps=MAX_STEPS,
        additional_authorized_imports=imports,
        verbosity_level=1,
        **kwargs,
    )
