"""Shared `go build` helper. This file registers no Reward Kit criteria."""

import fcntl
import subprocess
from pathlib import Path


def go_build(workspace: Path, args: list[str], timeout: int = 180) -> bool:
    """Run `go <args>` in the workspace. Concurrent builds take one lock."""
    if not workspace.is_dir():
        return False
    lock_path = Path("/tmp/titlecase-go-build.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            result = subprocess.run(
                ["go", *args],
                cwd=workspace,
                capture_output=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False

    return result.returncode == 0
    