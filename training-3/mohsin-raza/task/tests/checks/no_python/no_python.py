"""Check 2 (weight 1): no .py files anywhere AND the build passes.

The build condition stops a do-nothing agent that merely deletes files from scoring.
"""
import os
import subprocess
from pathlib import Path

from rewardkit import criterion


def compiles(workspace: Path) -> bool:
    """Everything compiles AND the repository root is a real `main` package."""
    env = {**os.environ, "GOTOOLCHAIN": "local"}
    try:
        name = subprocess.run(["go", "list", "-f", "{{.Name}}", "."], cwd=workspace, env=env,
                              capture_output=True, text=True, timeout=120)
        if name.returncode != 0 or name.stdout.strip() != "main":
            return False
        r = subprocess.run(["go", "build", "-o", os.devnull, "./..."], cwd=workspace, env=env,
                           capture_output=True, timeout=300)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0


@criterion(description="no .py files under the repository and the build passes")
def no_python_and_builds(workspace: Path) -> float:
    for _root, dirs, files in os.walk(workspace):
        if any(name.lower().endswith(".py") for name in files + dirs):
            return 0.0
    return 1.0 if compiles(workspace) else 0.0
