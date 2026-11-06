from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def go_build_passes(workspace: Path) -> bool:
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        timeout=120,
    )
    return result.returncode == 0
