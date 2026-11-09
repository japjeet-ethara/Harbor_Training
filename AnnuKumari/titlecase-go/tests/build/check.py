import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from go_build_util import go_build


@criterion
def build(workspace: Path) -> bool:
    """`go build ./...` in /workspace/repo passes."""
    return go_build(workspace, ["build", "./..."])
