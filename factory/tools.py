from smolagents import tool

# shared with runner.py; the tool bodies hardcode the same string (remote executors
# only see the function body, not module-level names)
PUNT_FILENAME = ".punt.json"


@tool
def write_file(path: str, content: str) -> str:
    """Write text content to a file (relative to the current workspace).

    Creates parent directories if they don't exist. Overwrites the file if it
    already exists.

    Args:
        path: Relative path within the workspace, e.g. 'notes.txt' or 'out/report.md'.
        content: The text content to write.
    """
    from pathlib import Path

    p = Path(path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {path}"


@tool
def read_file(path: str) -> str:
    """Read text content from a file (relative to the current workspace).

    Args:
        path: Relative path within the workspace.
    """
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")


@tool
def list_files(directory: str = ".") -> list[str]:
    """List filenames in a directory (relative to the current workspace).

    Args:
        directory: The directory to inspect. Defaults to the workspace root.
    """
    import os

    return sorted(os.listdir(directory))


@tool
def run_shell(command: str, timeout_s: int = 60) -> dict:
    """Execute a shell command in the current workspace and return its output.

    Use this for CLI tools that aren't accessible through Python stdlib:
    nmap, git, curl, ffmpeg, tar, unzip, etc.

    Args:
        command: The full shell command to execute (e.g., 'nmap -sV 127.0.0.1').
        timeout_s: Timeout in seconds. Defaults to 60.
    """
    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-3000:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Command timed out after {timeout_s}s", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"{type(e).__name__}: {e}", "returncode": -1}


@tool
def punt_to_human(reason: str, question: str) -> str:
    """Pause the task and wait for a human to answer a question you can't resolve alone.

    Call this ONLY when you truly cannot proceed without human input:
      - The task is ambiguous and only the user can clarify intent.
      - You need a secret/credential/config the user hasn't provided.
      - You need a decision that requires human judgment.

    The task will be saved to the review queue with your reason + question.
    A human will edit that file to add their answer. The task will then RESUME
    with their answer added to your context.

    Do NOT call this because a task is hard. Call it when a human answer would
    genuinely unblock you.

    Args:
        reason: One-sentence explanation of why you cannot proceed autonomously.
        question: The specific question you need the human to answer.
    """
    import json
    from pathlib import Path

    Path(".punt.json").write_text(
        json.dumps({"reason": reason, "question": question}, indent=2),
        encoding="utf-8",
    )
    return f"PUNTED_TO_HUMAN: {reason} | QUESTION: {question}"


from kb_tools import KB_TOOLS

ALL_TOOLS = [write_file, read_file, list_files, run_shell, punt_to_human, *KB_TOOLS]
