import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def _build_ok() -> bool:
    try:
        env = os.environ.copy()
        env["GOPROXY"] = "off"
        env["GOFLAGS"] = "-mod=readonly"
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=REPO,
            env=env,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@criterion
def build(workspace: Path) -> float:
    del workspace
    return 1.0 if _build_ok() else 0.0
