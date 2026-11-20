"""no_python: no .py files remain, and go build ./... passes."""

import subprocess
from pathlib import Path

from rewardkit import criterion
from score_utils import MIN_BEHAVIOUR_SCORE, score_behaviour


def go_build_ok(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@criterion
def no_python(workspace: Path) -> bool:
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return False
    return go_build_ok(workspace) and score_behaviour(workspace) >= MIN_BEHAVIOUR_SCORE
