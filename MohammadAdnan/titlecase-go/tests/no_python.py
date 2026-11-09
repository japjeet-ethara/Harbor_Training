from pathlib import Path
import subprocess
from rewardkit import criterion

@criterion
def no_python_files(workspace: Path) -> bool:
    has_python = any(workspace.rglob("*.py"))
    build = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace, capture_output=True, timeout=120
    )
    return not has_python and build.returncode == 0
