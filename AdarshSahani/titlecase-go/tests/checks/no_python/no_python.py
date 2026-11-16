"""Score 1 only when the build succeeds and no Python files remain."""

import subprocess
from pathlib import Path

from rewardkit.session import criterion


@criterion(description="No .py files under the workspace and go build ./... passes")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    try:
        build = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if build.returncode != 0:
        return False
    try:
        return not any(
            path.is_file() and path.suffix == ".py"
            for path in workspace.rglob("*")
        )
    except OSError:
        return False
