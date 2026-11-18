"""no_python (weight 1): no .py file left, the build passes, and the program
gets at least one hidden line right that it had to change.

The last condition stops a program that does nothing (or echoes its input, or
prints a memorised answer file) from earning this point by deleting files.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import grading  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="no .py files remain, the build passes, and the port does real work")
def python_removed(workspace: Path) -> bool:
    try:
        ws = Path(workspace)
        left = grading.py_files(ws)
        grading.log(f"[no_python] .py files left: {len(left)}")
        for p in left[:5]:
            grading.log(f"  {p}")
        if left or not grading.build_ok(ws):
            return False
        _matched, _total, changed = grading.hidden_results(ws)
        return changed > 0
    except Exception as exc:
        grading.log(f"[no_python] grader error: {exc!r}")
        return False
