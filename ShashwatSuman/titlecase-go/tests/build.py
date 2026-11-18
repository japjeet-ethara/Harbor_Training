"""Check 1 (weight 1): the Go module builds, using the standard library only."""

import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


@criterion(description="go build ./... passes and go.mod has no require lines")
def go_build(workspace: Path) -> bool:
    go_mod = workspace / "go.mod"
    if not go_mod.is_file():
        return False
    for line in go_mod.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("require"):
            return False  # third-party modules are not allowed
    # Build into a temporary directory: a bare `go build ./...` on a single main
    # package writes a binary into the repo, which collides with any leftover
    # `titlecase/` folder and would fail for reasons unrelated to the code.
    try:
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run(
                ["go", "build", "-o", out + "/", "./..."],
                cwd=workspace, capture_output=True, timeout=300,
            )
    except Exception:
        return False
    return result.returncode == 0
