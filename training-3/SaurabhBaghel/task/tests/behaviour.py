"""Exact output on the expanded grading exam.

The candidate is compiled with cgo disabled and executed in a chroot that
contains only that static binary. It cannot read the fixture, the original
package, or a Python interpreter.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import go_build  # noqa: E402

EXAM_INPUTS = Path("/tests/data/inputs.txt")
EXAM_ANSWERS = Path("/tests/data/answers.txt")


@criterion
def behaviour(workspace: Path) -> float:
    try:
        if not workspace.is_dir() or not EXAM_INPUTS.is_file() or not EXAM_ANSWERS.is_file():
            return 0.0
        jail = Path(tempfile.mkdtemp(prefix="titlecase-jail-"))
        binary = jail / "titlecase"
        built = go_build(workspace, "-o", str(binary), ".")
        if built.returncode != 0 or not binary.is_file():
            return 0.0
        os.chmod(binary, 0o755)
        inputs = EXAM_INPUTS.read_bytes()
        proc = subprocess.run(
            ["chroot", str(jail), "/titlecase"],
            input=inputs,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return 0.0
        expected = EXAM_ANSWERS.read_bytes()
        return 1.0 if expected and proc.stdout == expected else 0.0
    except Exception:
        return 0.0
