"""no_python: no .py files are left, the build passes, AND the program gets
real titles right.

Before Day 5 this check paid 1.0 for "no .py files and it builds", so deleting
the Python files next to an empty Go program earned 1/6 of the reward. Now it
pays the behaviour score, and only when no .py file remains and the build passes.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, "/tests/lib")
import grading  # noqa: E402


@rk.criterion(description="No .py files remain, go build ./... passes, and output is correct")
def no_python_files(workspace: Path) -> float:
    if grading.has_python_files(workspace):
        return 0.0
    if not grading.go_build_all(workspace):
        return 0.0
    return grading.behaviour_score(workspace)
