from pathlib import Path
import subprocess
from rewardkit import criterion


@criterion(description="no .py files remain under /workspace/repo and go build ./... passes")
def no_python_and_builds(workspace: Path) -> bool:
    py_files = list(workspace.rglob("*.py"))
    if py_files:
        return False

    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0

