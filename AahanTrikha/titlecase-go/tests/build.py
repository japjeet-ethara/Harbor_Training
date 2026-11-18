import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


@criterion
def build(workspace: Path) -> bool:
    return REPO.is_dir() and subprocess.run(
        ["go", "build", "./..."], cwd=REPO,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0
