"""Score 1 when `go build ./...` succeeds in the workspace."""

import subprocess
from pathlib import Path

from rewardkit import criterion

_TIMEOUT_SEC = 180


@criterion(description="go build ./... succeeds in /workspace/repo")
def build(workspace: Path) -> bool:
    if not workspace.is_dir():
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
