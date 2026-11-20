"""Score 1 when `go build ./...` succeeds in the repository."""

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


@criterion
def build(workspace: Path) -> float:
    del workspace
    if not REPO.is_dir():
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
