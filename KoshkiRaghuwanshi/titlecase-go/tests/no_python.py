import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion

from go_run import go


@criterion
def no_python(workspace: Path) -> float:
    has_python = any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file())
    if has_python:
        return 0.0
    result = go(workspace, "go build ./...")
    return 1.0 if result is not None and result.returncode == 0 else 0.0
