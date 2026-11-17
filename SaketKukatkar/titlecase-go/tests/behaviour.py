"""Check 3 (weight 4): output matches the original Python on the HIDDEN inputs.

Score = share of hidden lines whose output is byte-for-byte equal to
tests/data/hidden_expected.txt (answers frozen from the original Python code).
"""
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk

DATA = Path("/tests/data")
if not DATA.is_dir():  # local runs
    DATA = Path(__file__).resolve().parent / "data"


@rk.criterion(description="share of hidden titles titlecased exactly like the original")
def behaviour(workspace: Path) -> float:
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")
    if expected and expected[-1] == b"":
        expected.pop()

    with tempfile.TemporaryDirectory() as tmp:
        exe = str(Path(tmp) / "titlecase_bin")
        try:
            b = subprocess.run(["go", "build", "-o", exe, "."], cwd=workspace,
                               capture_output=True, timeout=300)
        except (OSError, subprocess.SubprocessError):
            return 0.0
        if b.returncode != 0:
            return 0.0
        try:
            r = subprocess.run([exe], input=inputs, capture_output=True, timeout=120)
        except (OSError, subprocess.SubprocessError):
            return 0.0

    got = r.stdout.split(b"\n")
    if got and got[-1] == b"":
        got.pop()
    hits = sum(1 for i, e in enumerate(expected) if i < len(got) and got[i] == e)
    return hits / len(expected)
