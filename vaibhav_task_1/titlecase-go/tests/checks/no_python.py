"""no_python (weight 1): no .py file anywhere under the workspace AND the build
passes -> 1, else 0. Gated on the build so a do-nothing agent that only
deletes files gets no free points."""
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


def _builds(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    try:
        r = subprocess.run(["go", "build", "./..."], cwd=workspace, env=_go_env(),
                           capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


@criterion(description="no .py files left under the workspace, and the build passes")
def no_python(workspace: Path) -> bool:
    workspace = Path(workspace)
    for root, _dirs, files in os.walk(workspace):
        if any(f.endswith(".py") for f in files):
            return False
    return _builds(workspace)
