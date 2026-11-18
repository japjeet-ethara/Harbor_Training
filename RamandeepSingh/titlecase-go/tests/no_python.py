"""
Criterion 2: no_python (weight 1)
Check that no .py files remain anywhere under /workspace/repo,
AND the Go build succeeds. Score 1 if both conditions are satisfied, otherwise 0.
"""

import subprocess
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_no_python(workspace: Path) -> float:
    try:
        # Check that no .py files exist anywhere under workspace (case-insensitive)
        py_files = [
            p for p in workspace.rglob("*")
            if p.is_file() and p.name.lower().endswith(".py")
        ]
        if py_files:
            return 0.0

        # Check that Go build succeeds
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
    print(check_no_python(target))
