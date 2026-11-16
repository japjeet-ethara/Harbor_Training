"""Build check: `go build ./...` must succeed in the submitted repository."""

from pathlib import Path
import subprocess

from rewardkit import criterion

BUILD_TIMEOUT_SEC = 300


def _build_passes(workspace: Path) -> bool:
    try:
        completed = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=BUILD_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


@criterion
def build_passes(workspace: Path) -> float:
    try:
        return 1.0 if _build_passes(workspace) else 0.0
    except Exception:
        return 0.0
