"""build (weight 1): `go build ./...` passes, imports are allowed, AND the
program really titlecases (behaviour >= GATE) -> 1, else 0.

The gate stops a do-nothing program from collecting this point (Day 4 cheat 3).
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
import grade  # noqa: E402  (/tests/lib/grade.py)


@rk.criterion(description="`go build ./...` succeeds (paid only if behaviour >= 0.5)")
def go_build_passes(workspace: Path) -> bool:
    r = grade.grade(workspace)
    return r["built"] and grade.gated(r)
