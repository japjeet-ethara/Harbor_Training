"""Check 3 (weight 4): share of output lines that exactly match the original Python.

Uses the HIDDEN set only (data/hidden_inputs.txt vs data/hidden_expected.txt).
"""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

TESTS_DIR = Path(os.environ.get("TESTS_DIR", "/tests"))


@criterion(description="share of hidden titles whose output matches Python byte for byte")
def hidden_lines_match(workspace: Path) -> float:
    inputs = (TESTS_DIR / "data" / "hidden_inputs.txt").read_bytes()
    expected = (TESTS_DIR / "data" / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    env = {**os.environ, "GOTOOLCHAIN": "local"}
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "titlecase-bin")
        try:
            b = subprocess.run(["go", "build", "-o", exe, "."], cwd=workspace, env=env,
                               capture_output=True, timeout=300)
            if b.returncode != 0:
                return 0.0
            r = subprocess.run([exe], input=inputs, capture_output=True, timeout=300, cwd=tmp)
        except (subprocess.TimeoutExpired, OSError):
            return 0.0
    actual = r.stdout.split(b"\n")
    if actual and actual[-1] == b"":
        actual = actual[:-1]
    matched = sum(1 for e, a in zip(expected, actual) if e == a)
    return matched / len(expected)
