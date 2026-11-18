"""build (weight 1): `go build ./...` in /workspace/repo passes -> 1, else 0."""
import shutil
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk


@rk.criterion(description="`go build ./...` succeeds in the repository")
def go_build_passes(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    # Build a private copy so parallel checks never race on the output binary
    # that `go build ./...` writes for a single main package.
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(workspace, repo, symlinks=True)
        try:
            r = subprocess.run(["go", "build", "./..."], cwd=repo,
                               capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return False
    if r.returncode != 0:
        print("go build failed:\n" + r.stderr[-2000:])
    return r.returncode == 0
