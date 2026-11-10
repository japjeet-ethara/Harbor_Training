"""Build criterion for the Titlecase Go Harbor task."""

import os
from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def build(workspace: Path) -> float:
    """Return 1.0 if go build ./... succeeds, otherwise 0.0."""

    repo_dir = Path("/workspace/repo")

    if not repo_dir.exists():
        repo_dir = workspace

    if not repo_dir.exists():
        return 0.0

    env = os.environ.copy()
    env["CGO_ENABLED"] = "0"

    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        return 1.0 if result.returncode == 0 else 0.0

    except (OSError, subprocess.TimeoutExpired):
        return 0.0