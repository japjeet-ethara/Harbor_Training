import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def _build_ok() -> bool:
    try:
        env = os.environ.copy()
        env["GOPROXY"] = "off"
        env["GOFLAGS"] = "-mod=readonly"
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=REPO,
            env=env,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _has_python(repo: Path) -> bool:
    if not repo.is_dir():
        return True
    return any(path.is_file() and path.name.endswith(".py") for path in repo.rglob("*"))


@criterion
def no_python(workspace: Path) -> float:
    del workspace
    if _has_python(REPO) or not _build_ok():
        return 0.0
    return 1.0
