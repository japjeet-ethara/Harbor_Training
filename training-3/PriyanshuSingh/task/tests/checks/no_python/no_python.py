"""no_python: no .py files are left AND the build passes.

The build condition stops a do-nothing agent from earning points by deleting
files.
"""
import subprocess
from pathlib import Path

import rewardkit as rk


@rk.criterion(description="No .py files remain and go build ./... passes")
def no_python_files(workspace: Path) -> bool:
    if any(workspace.rglob("*.py")):
        return False
    build = subprocess.run(
        ["go", "build", "./..."], cwd=workspace, capture_output=True, timeout=300
    )
    return build.returncode == 0
