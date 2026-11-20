import sys
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _grade  # noqa: E402


@criterion(description="go build ./... passes; counts only as far as the port is correct")
def go_build_passes(workspace: Path) -> float:
    if not _grade.go_build_all(workspace):
        return 0.0
    return _grade.behaviour_score(workspace)


rk.go_build_passes()
