import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion

from go_run import go


@criterion
def build(workspace: Path) -> float:
    result = go(workspace, "go build ./...")
    return 1.0 if result is not None and result.returncode == 0 else 0.0
