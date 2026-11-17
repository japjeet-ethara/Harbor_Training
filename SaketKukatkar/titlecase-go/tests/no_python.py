"""Check 2 (weight 1): no .py file anywhere under the repo AND the build passes.

The build condition stops a do-nothing / delete-only agent from collecting free points.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk


def _builds(workspace: Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run(["go", "build", "-o", tmp + "/", "./..."],
                               cwd=workspace, capture_output=True, timeout=300)
        except (OSError, subprocess.SubprocessError):
            return False
    return r.returncode == 0


@rk.criterion(description="no .py files remain under /workspace/repo and the build passes")
def no_python(workspace: Path) -> bool:
    for _root, _dirs, files in os.walk(workspace):
        for name in files:
            if name.lower().endswith(".py"):
                return False
    return _builds(workspace)
