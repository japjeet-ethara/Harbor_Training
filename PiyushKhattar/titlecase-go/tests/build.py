import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion
def build(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            timeout=120,
            capture_output=True,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0
