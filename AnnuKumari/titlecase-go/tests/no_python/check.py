import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from go_build_util import go_build


@criterion
def no_python(workspace: Path) -> bool:
    """No .py files remain under the repo, and `go build ./...` passes."""
    if not workspace.is_dir():
        return False
    if any(workspace.rglob("*.py")):
        return False
    return go_build(workspace, ["build", "./..."])
