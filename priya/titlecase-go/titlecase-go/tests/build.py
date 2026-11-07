"""go build ./... must succeed in the repository."""

import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion
def build(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
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
