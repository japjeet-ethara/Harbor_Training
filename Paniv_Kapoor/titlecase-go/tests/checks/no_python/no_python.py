"""Score 1 only when the workspace has no Python files and still builds."""

import subprocess
from pathlib import Path

from rewardkit import criterion

_TIMEOUT_SEC = 180


def _has_python_files(workspace: Path) -> bool:
    for path in workspace.rglob("*"):
        if path.is_file() and path.suffix == ".py":
            return True
    return False


@criterion(description="no .py files remain and go build ./... succeeds")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    try:
        if _has_python_files(workspace):
            return False
    except OSError:
        return False
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0
