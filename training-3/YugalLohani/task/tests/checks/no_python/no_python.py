"""no_python (weight 1): no .py file left, the build passes, and the Go port
actually works (at least NO_PYTHON_MIN_BEHAVIOUR of hidden lines correct).

Tying the point to real, near-complete behaviour stops a program that does
nothing, echoes its input, prints a memorised answer file, or only ports the
easy rules from earning it by deleting the .py files.
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
        matched, total, _changed = grading.hidden_results(ws)
        # Pay only for a Python-free port that actually works, not for deleting
        # files or a trivial/partial program.
        return total > 0 and matched / total >= grading.NO_PYTHON_MIN_BEHAVIOUR
    except Exception as exc:
        grading.log(f"[no_python] grader error: {exc!r}")
        return False
