import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path(os.environ.get("TITLECASE_REPO", "/workspace/repo"))


@criterion
def no_python(workspace: Path) -> bool:
    del workspace
    built = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        return False
    return not any(REPO.rglob("*.py"))
