"""Check 1 (weight 1): `go build ./...` passes in /workspace/repo (output discarded with -o /dev/null so a leftover
folder named like the binary cannot cause a false failure)."""
import os
import subprocess

import rewardkit as rk


@rk.criterion(description="`go build ./...` passes in the repository")
def build(workspace) -> bool:
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off",
               GOTOOLCHAIN="local", GOCACHE="/tmp/gocache-build", CGO_ENABLED="0")
    if not (workspace / "go.mod").is_file():
        return False
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace, env=env,
                           capture_output=True, timeout=240)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0
