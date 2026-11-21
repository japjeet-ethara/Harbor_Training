"""Check 2 - no_python (weight 1).

1 if no .py file exists anywhere under /workspace/repo AND the build check
passes AND at least half of the exam lines are correct; else 0.

The gates stop cheap cheats: deleting the .py files only pays when the Go port
really works, so "trivial Go program + delete .py" earns nothing here. Python
is not installed where the program runs, so a Go wrapper around a renamed
copy of the original also gets 0 lines right.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="no .py files, the build passes, and at least half the exam lines are correct")
def no_python_files(workspace: Path) -> dict:
    py_files = common.find_py_files(workspace)
    if py_files:
        shown = ", ".join(py_files[:10])
        return {"score": False, "reasoning": f"{len(py_files)} .py file(s) left: {shown}"}
    ok, why = common.build_status(workspace)
    if not ok:
        return {"score": False, "reasoning": f"no .py files, but the build fails: {why}"}
    share, why = common.behaviour_share(workspace)
    if share < common.NO_PYTHON_MIN_SHARE:
        return {"score": False, "reasoning": (
            f"no .py files and the build passes, but only {share:.2%} of exam lines "
            f"are correct (needs {common.NO_PYTHON_MIN_SHARE:.0%})")}
    return {"score": True, "reasoning": f"no .py files, the build passes, {share:.2%} of exam lines correct"}
