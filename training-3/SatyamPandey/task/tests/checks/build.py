"""Check `build` (weight 0, shown for diagnosis): `go build ./...` passes in /workspace/repo.

It earns no points on its own (Day 5 fix for cheats 1 and 2): `behaviour` is the
only scored check, and it already requires a passing build.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules import go_build  # noqa: E402


@rk.criterion(description="`go build ./...` passes in the repository (diagnostic, weight 0)")
def build(workspace) -> bool:
    # -o /dev/null: the module is called `titlecase` and an emptied titlecase/ folder may remain.
    return go_build(workspace, "/dev/null", "./...")
