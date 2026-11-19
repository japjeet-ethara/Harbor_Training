"""build gate (report-only; weight 0 in reward.toml): `go build ./...` passes -> 1, else 0.

It no longer pays points on its own: behaviour is 0 unless this gate passes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import go_build_all  # noqa: E402

import rewardkit as rk  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="`go build ./...` passes in /workspace/repo")
def go_build_passes(workspace: Path) -> bool:
    return go_build_all(workspace)


rk.go_build_passes()
