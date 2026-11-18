"""no_python (weight 1): no .py files anywhere under /workspace/repo AND the
build passes -> 1, else 0.

Gated on the build so that an agent which only deletes files (and builds
nothing) gets no free points.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk


@rk.criterion(description="No .py files remain and `go build ./...` succeeds")
def no_python_and_builds(workspace: Path) -> bool:
    leftovers = [p for p in workspace.rglob("*") if p.suffix.lower() == ".py"]
    if leftovers:
        print("Python files left:", *[str(p) for p in leftovers[:20]], sep="\n  ")
        return False
    if not (workspace / "go.mod").is_file():
        return False
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(workspace, repo, symlinks=True)
        try:
            r = subprocess.run(["go", "build", "./..."], cwd=repo,
                               capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return False
    return r.returncode == 0
