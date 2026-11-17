"""No-Python check: no `.py` files may remain, and the build must pass."""

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


def _has_python_files(workspace: Path) -> bool:
    try:
        for _ in workspace.rglob("*.py"):
            return True
    except OSError:
        return True
    return False


@criterion
def no_python_files(workspace: Path) -> float:
    try:
        if not _build_passes(workspace):
            return 0.0
        return 0.0 if _has_python_files(workspace) else 1.0
    except Exception:
        return 0.0
