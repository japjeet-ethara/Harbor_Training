import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


@criterion
def no_python(workspace: Path) -> bool:
    if not REPO.is_dir():
        return False
    build = subprocess.run(
        ["go", "build", "./..."], cwd=REPO,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if build.returncode != 0:
        return False
    found = subprocess.run(
        ["find", str(REPO), "-type", "f", "-name", "*.py", "-print"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return found.returncode == 0 and found.stdout == b""
