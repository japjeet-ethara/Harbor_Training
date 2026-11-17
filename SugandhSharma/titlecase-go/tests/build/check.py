"""Check 1, weight 1: the Go code in the repository builds, offline, with the Go toolchain of the image."""
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


@criterion(description="go build ./... passes in the repository")
def build(workspace: Path) -> bool:
    return go_build_passes(workspace)
