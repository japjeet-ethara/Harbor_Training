"""Check 2 (weight 1): no .py file anywhere under the repo AND the build passes.

The build condition stops a do-nothing / delete-everything agent from earning free points.
"""
import os
import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion(description="No .py files remain under the repository and `go build ./...` passes")
def no_python(workspace: Path) -> bool:
    for _root, _dirs, files in os.walk(workspace):
        if any(f.lower().endswith(".py") for f in files):
            return False
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0
