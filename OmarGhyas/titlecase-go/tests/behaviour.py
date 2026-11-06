"""Score the fraction of hidden cases the workspace program matches exactly."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion
from support import behaviour_score


@criterion
def behaviour(workspace: Path) -> float:
    return behaviour_score(workspace)
