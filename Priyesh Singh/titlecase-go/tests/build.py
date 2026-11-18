import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path(os.environ.get("TITLECASE_REPO", "/workspace/repo"))


@criterion
def build(workspace: Path) -> bool:
    del workspace
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
