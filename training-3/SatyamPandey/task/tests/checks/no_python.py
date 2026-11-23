"""Check `no_python` (weight 0, shown for diagnosis): the hard rules hold and the build passes.

It earns no points on its own (Day 5 fix for cheats 1 and 2): deleting the .py files
and writing an empty Go program used to be worth 2/6 = 0.33. The same rules are now
a gate inside `behaviour`, see rules.py.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules import go_build, rules_ok  # noqa: E402


@rk.criterion(description="no Python files, stdlib only, no starting programs, builds (diagnostic, weight 0)")
def no_python(workspace) -> bool:
    ok, _reason = rules_ok(workspace)
    return ok and go_build(workspace, "/dev/null", "./...")
