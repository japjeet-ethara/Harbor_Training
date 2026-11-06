"""No Python sources remain, and the Go module still builds.

The build requirement is intentional: deleting the Python tree alone is not
a solution.
"""

import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import go_build  # noqa: E402


@criterion
def no_python(workspace: Path) -> float:
    try:
        if not workspace.is_dir():
            return 0.0
        if any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file()):
            return 0.0
        result = go_build(workspace, "./...")
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0
