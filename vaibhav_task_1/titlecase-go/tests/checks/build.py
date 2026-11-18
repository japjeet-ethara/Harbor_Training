"""build (weight 1): `go build ./...` in the workspace passes -> 1, else 0."""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


def _go_env():
    env = dict(os.environ)
    env.update(GOTOOLCHAIN="local", GOPROXY="off", GOFLAGS="-mod=mod",
               GOWORK="off", CGO_ENABLED="0")
    env.setdefault("GOCACHE", os.path.join(tempfile.gettempdir(), "tc-gocache"))
    env["PATH"] = env.get("PATH", "") + os.pathsep + "/usr/local/go/bin"
    return env


@criterion(description="go build ./... passes in the workspace")
def build(workspace: Path) -> bool:
    if not (Path(workspace) / "go.mod").is_file():
        return False
    try:
        r = subprocess.run(["go", "build", "./..."], cwd=workspace, env=_go_env(),
                           capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0
