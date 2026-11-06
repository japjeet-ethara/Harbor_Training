"""no_python: 1 if the repo has no .py files and the build passes, else 0."""

import os
import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion(description="No .py files under the repo, and `go build ./...` passes")
def no_python_files(workspace: Path) -> bool:
    for _, _, files in os.walk(workspace):
        if any(name.endswith(".py") for name in files):
            return False
    try:
        build = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False
    return build.returncode == 0
