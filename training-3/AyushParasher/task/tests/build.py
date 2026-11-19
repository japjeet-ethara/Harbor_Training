import subprocess
from pathlib import Path
import rewardkit as rk
from rewardkit import criterion

@criterion(description="go build ./... passes")
def go_build_passes(workspace: Path) -> bool:
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace,
                           capture_output=True, timeout=600)
    except Exception:
        return False
    return r.returncode == 0

rk.go_build_passes()
