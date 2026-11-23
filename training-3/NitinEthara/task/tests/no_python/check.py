"""Check 2 (weight 1): no .py files and exact behavior on the frozen exam.

This prevents deleting the Python source and compiling an unrelated placeholder from
earning structural reward.
"""
import os
import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality import exact_exam_passes


@criterion(description="No .py files remain and the program exactly passes the frozen exam")
def no_python(workspace: Path) -> bool:
    for _root, _dirs, files in os.walk(workspace):
        if any(f.lower().endswith(".py") for f in files):
            return False
    return exact_exam_passes(workspace)
