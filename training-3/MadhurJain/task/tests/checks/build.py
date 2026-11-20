import subprocess
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

_TIMEOUT_SEC = 300


def _stdlib_only(workspace: Path) -> bool:
    go_mod = workspace / "go.mod"
    if not go_mod.is_file() or (workspace / "vendor").exists():
        return False
    for line in go_mod.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("require"):
            return False
    return True


@criterion
def build(workspace: Path) -> bool:
    if not _stdlib_only(workspace):
        return False
    try:
        result = subprocess.run(
            ["go", "build", "-o", "/dev/null", "./..."],
            cwd=workspace,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


rk.build()
