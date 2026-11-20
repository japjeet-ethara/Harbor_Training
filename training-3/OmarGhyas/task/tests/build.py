"""Score 1.0 when `go build ./...` succeeds in the agent workspace."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion
from support import go_build_succeeds


@criterion
def build(workspace: Path) -> float:
    return 1.0 if go_build_succeeds(workspace) else 0.0
