"""No Python files may remain, and the Go build must still pass."""

import subprocess
from pathlib import Path

from rewardkit import criterion


def _build_passes(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@criterion
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return False
    return _build_passes(workspace)
