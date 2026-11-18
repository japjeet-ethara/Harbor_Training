import subprocess
from pathlib import Path

from rewardkit import criterion


@criterion
def no_python(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            timeout=120,
            capture_output=True,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    return not any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file())
