"""Exact output on the hidden fixture.

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

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


@criterion
def behaviour(workspace: Path) -> float:
    try:
        if not workspace.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
            return 0.0
        jail = Path(tempfile.mkdtemp(prefix="titlecase-jail-"))
        binary = jail / "titlecase"
        built = go_build(workspace, "-o", str(binary), ".")
        if built.returncode != 0 or not binary.is_file():
            return 0.0
        os.chmod(binary, 0o755)
        inputs = HIDDEN_INPUTS.read_bytes()
        proc = subprocess.run(
            ["chroot", str(jail), "/titlecase"],
            input=inputs,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return 0.0
        expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
        actual = proc.stdout.decode("utf-8").splitlines()
        if not expected:
            return 0.0
        matches = sum(got == want for got, want in zip(actual, expected))
        return matches / len(expected)
    except Exception:
        return 0.0
