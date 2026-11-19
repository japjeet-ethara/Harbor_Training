import subprocess
from pathlib import Path

from rewardkit import criterion


def _has_python_file(workspace: Path) -> bool:
    for path in workspace.rglob("*"):
        if path.name.lower().endswith(".py") and not path.is_dir():
            return True
    return False


@criterion
def no_python_sources(workspace: Path) -> float:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=240,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if result.returncode != 0 or _has_python_file(workspace):
        return 0.0
    return 1.0
