"""Check 2 (weight 1): no .py files are left, AND the Go build passes.

The build condition matters: without it, an agent that only deletes files
(and builds nothing) would collect free points.
"""

import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


@criterion(description="no .py files anywhere in the repository and the Go build passes")
def no_python_left(workspace: Path) -> bool:
    if any(p.is_file() for p in workspace.rglob("*.py")):
        return False
    if not (workspace / "go.mod").is_file():
        return False
    try:
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run(
                ["go", "build", "-o", out + "/", "./..."],
                cwd=workspace, capture_output=True, timeout=300,
            )
    except Exception:
        return False
    return result.returncode == 0
