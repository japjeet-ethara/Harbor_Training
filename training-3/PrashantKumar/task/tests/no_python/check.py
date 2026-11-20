from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def no_python_files_after_successful_build(workspace: Path) -> bool:
    build = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        timeout=120,
    )

    if build.returncode != 0:
        return False

    return not any(workspace.rglob("*.py"))
