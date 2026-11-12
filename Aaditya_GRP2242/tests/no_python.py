"""No Python sources left behind, and the tree still builds."""

import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def _build_passes(repo: Path) -> bool:
    proc = subprocess.run(
        ["go", "build", "./..."],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.returncode == 0


@criterion
def no_python_files(workspace: Path) -> float:
    del workspace
    try:
        if not REPO.is_dir():
            return 0.0
        if any(REPO.rglob("*.py")):
            return 0.0
        return 1.0 if _build_passes(REPO) else 0.0
    except Exception:
        return 0.0
