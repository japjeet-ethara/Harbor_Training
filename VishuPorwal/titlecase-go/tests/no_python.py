"""Score 1 only when the repository has no .py files and `go build ./...` passes."""

import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def _go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOCACHE"] = tempfile.mkdtemp(prefix="go-cache-")
    env["CGO_ENABLED"] = "0"
    env["GOTOOLCHAIN"] = "local"
    return env


def _has_python(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix == ".py":
            return True
    return False


@criterion
def no_python(workspace: Path) -> float:
    del workspace
    if not REPO.is_dir() or _has_python(REPO):
        return 0.0
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=REPO,
            env=_go_env(),
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    return 1.0 if result.returncode == 0 else 0.0
