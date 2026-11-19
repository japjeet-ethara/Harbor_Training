"""Check 2, weight 1: no .py file is left anywhere in the repository AND the Go build passes.

The build is part of this check on purpose: without it, an attempt that only deletes files would be paid.
"""
import os
import subprocess
from pathlib import Path

from rewardkit import criterion

GO_ENV = {"GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}


def go_build_passes(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    try:
        done = subprocess.run(["go", "build", "./..."], cwd=workspace, env={**os.environ, **GO_ENV},
                              capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


@criterion(description="no .py file is left in the repository and the Go build passes")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    for _root, _dirs, files in os.walk(workspace):
        if any(name.lower().endswith(".py") for name in files):
            return False
    return go_build_passes(workspace)
