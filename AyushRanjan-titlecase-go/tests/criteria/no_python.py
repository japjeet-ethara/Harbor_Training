"""Check that the repository contains no Python files and builds successfully."""

import os
from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def no_python(workspace: Path) -> float:
    repo_dir = Path("/workspace/repo")

    if not repo_dir.exists():
        repo_dir = workspace

    if not repo_dir.exists():
        return 0.0

    # Check for any .py files recursively.
    python_files = list(repo_dir.rglob("*.py"))

    if python_files:
        return 0.0

    # Confirm that the Go project builds.
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