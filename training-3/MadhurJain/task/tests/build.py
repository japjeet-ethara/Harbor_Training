import subprocess
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

_TIMEOUT_SEC = 120


@criterion
def build(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "-o", "/dev/null", "./..."],
            cwd=workspace,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


rk.build()
