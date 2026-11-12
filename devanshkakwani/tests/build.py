from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def build(workspace: Path) -> bool:
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0
