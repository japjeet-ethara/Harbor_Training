"""Check 2 (weight 1): no .py file anywhere under /workspace/repo AND the build passes -> 1, else 0.

The build condition stops a do-nothing / delete-everything agent from earning free points.
"""
import os
import subprocess
from pathlib import Path

import rewardkit as rk


def _has_python_files(root: Path) -> bool:
    for _dirpath, _dirnames, filenames in os.walk(root):  # includes hidden dirs
        if any(name.endswith(".py") for name in filenames):
            return True
    return False


@rk.criterion(description="no .py files remain under the repository and `go build ./...` passes")
def no_python_and_builds(workspace: Path) -> bool:
    if not workspace.is_dir() or _has_python_files(workspace):
        return False
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off", GOTOOLCHAIN="local",
               GOCACHE="/tmp/go-build-cache-verifier-nopy", CGO_ENABLED="0")
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace, env=env,
                           capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


rk.no_python_and_builds()
