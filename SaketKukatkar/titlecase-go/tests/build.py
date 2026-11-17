"""Check 1 (weight 1): the whole module compiles, i.e. `go build ./...` passes.

The executable is written into a temporary directory so that its name (taken
from the module name) can never collide with a directory in the repository.
"""
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk


@rk.criterion(description="go build ./... passes in /workspace/repo")
def build(workspace: Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run(["go", "build", "-o", tmp + "/", "./..."],
                               cwd=workspace, capture_output=True, timeout=300)
        except (OSError, subprocess.SubprocessError):
            return False
    return r.returncode == 0
