"""Check 1 - build (weight 1).

1 if /workspace/repo has a go.mod without `require` directives (standard
library only) and `go build ./...` passes; else 0.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="go build ./... passes and go.mod has no require directives")
def go_build_passes(workspace: Path) -> dict:
    ok, why = common.build_status(workspace)
    return {"score": ok, "reasoning": why}
