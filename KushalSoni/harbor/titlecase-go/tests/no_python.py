"""Score 1 only when the repository builds and contains no Python files."""

import os
import subprocess
from pathlib import Path

from rewardkit import criterion


def go_build_ok(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:" + env.get("PATH", "/usr/local/bin:/usr/bin:/bin")
    env.setdefault("GOTOOLCHAIN", "local")
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@criterion
def no_python(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0
    if any(path.is_file() and path.suffix == ".py" for path in workspace.rglob("*")):
        return 0.0
    return 1.0 if go_build_ok(workspace) else 0.0
