"""go build ./... in the workspace passes."""

import fcntl
import subprocess
from contextlib import contextmanager
from pathlib import Path

from rewardkit import criterion

BUILD_TIMEOUT_SEC = 120


@contextmanager
def go_lock():
    lock_path = Path("/tmp/rewardkit-go.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def go_build_passes(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    try:
        with go_lock():
            result = subprocess.run(
                ["go", "build", "-o", "/tmp/titlecase-build", "./..."],
                cwd=workspace,
                capture_output=True,
                timeout=BUILD_TIMEOUT_SEC,
            )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@criterion
def build(workspace: Path) -> bool:
    return go_build_passes(workspace)
