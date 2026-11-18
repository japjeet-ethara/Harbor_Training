import subprocess
from pathlib import Path
import rewardkit as rk
from rewardkit import criterion

@criterion(description="no .py files remain and go build ./... passes")
def python_removed(workspace: Path) -> bool:
    if any(workspace.rglob("*.py")):
        return False
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace,
                           capture_output=True, timeout=600)
    except Exception:
        return False
    return r.returncode == 0

rk.python_removed()
