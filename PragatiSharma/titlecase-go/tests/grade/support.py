"""Shared Go grading helpers. This module registers no Reward Kit criteria."""

import subprocess
import sys
from pathlib import Path

BUILD_TIMEOUT_SEC = 60
RUN_TIMEOUT_SEC = 60
HIDDEN_RECORD_COUNT = 2000


def log(message: str) -> None:
    print(message, file=sys.stderr)


def records(data: bytes) -> list[bytes]:
    """Split on LF only. Keep spaces and blank lines. Drop one trailing LF."""
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


def run_command(
    args: list[str],
    cwd: Path,
    timeout: int,
    stdin: bytes | None = None,
) -> tuple[int | None, bytes, bytes, bool]:
    """Run a command. Stdout and stderr stay separate. A timeout is not an exception."""
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
        stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
        return None, stdout, stderr, True
    except OSError as exc:
        return None, b"", str(exc).encode(), False
    return completed.returncode, completed.stdout, completed.stderr, False


def go_build_all(workspace: Path) -> tuple[bool, str]:
    if not workspace.is_dir():
        return False, f"workspace is not a directory: {workspace}"
    code, _stdout, stderr, timed_out = run_command(
        ["go", "build", "./..."],
        workspace,
        BUILD_TIMEOUT_SEC,
    )
    if timed_out:
        return False, f"go build ./... timed out after {BUILD_TIMEOUT_SEC}s"
    if code != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        return False, detail or f"go build ./... exited {code}"
    return True, "go build ./... succeeded"
