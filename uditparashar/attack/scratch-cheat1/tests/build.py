"""Check 1 (weight 1): `go build ./...` passes in /workspace/repo -> 1, else 0."""
import os
import subprocess
from pathlib import Path

import rewardkit as rk


@rk.criterion(description="`go build ./...` succeeds in the repository")
def go_build_passes(workspace: Path) -> bool:
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off", GOTOOLCHAIN="local",
               GOCACHE="/tmp/go-build-cache-verifier-build", CGO_ENABLED="0")
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace, env=env,
                           capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


rk.go_build_passes()
