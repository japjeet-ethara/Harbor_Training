"""Build check: `go build ./...` in the repository."""

import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import go_build  # noqa: E402


@criterion
def build(workspace: Path) -> float:
    try:
        if not workspace.is_dir():
            return 0.0
        result = go_build(workspace, "./...")
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0
