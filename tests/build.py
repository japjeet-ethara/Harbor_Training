"""
Criterion 1: build (weight 1)
Run `go build ./...` inside `/workspace/repo`.
Score 1 if it succeeds, otherwise 0.
"""

import subprocess
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_build(workspace: Path) -> float:
    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        return 1.0 if res.returncode == 0 else 0.0
    except Exception:
        return 0.0


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/repo")
    print(check_build(target))
