from pathlib import Path
import subprocess
from rewardkit import criterion

REPO_DIR = Path("/workspace/repo")


@criterion
def check_build(workspace: Path) -> float:
    repo_path = REPO_DIR if REPO_DIR.exists() else workspace
    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        return 1.0 if res.returncode == 0 else 0.0
    except Exception:
        return 0.0
