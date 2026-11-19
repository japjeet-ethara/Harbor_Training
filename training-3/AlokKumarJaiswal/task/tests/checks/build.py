import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion
def go_build(workspace: Path) -> float:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=240,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    return 1.0 if result.returncode == 0 else 0.0
