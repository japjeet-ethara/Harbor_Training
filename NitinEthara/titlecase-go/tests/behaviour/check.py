"""Check 3 (weight 4): share of HIDDEN titles whose output matches the original byte for byte.

Builds the program at the repo root, feeds it tests/data/hidden_inputs.txt and compares
line i of the output with line i of tests/data/hidden_expected.txt (frozen from the
ORIGINAL Python titlecase by tests/gen.py). Extra or missing lines lower the score.
"""
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

DATA = Path(__file__).resolve().parent.parent / "data"


@criterion(description="Share of hidden titles whose output equals the original titlecase() byte for byte")
def behaviour(workspace: Path) -> float:
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "titlecase"
        try:
            b = subprocess.run(["go", "build", "-o", str(exe), "."], cwd=workspace,
                               capture_output=True, timeout=300)
            if b.returncode != 0 or not exe.exists():
                return 0.0
            p = subprocess.run([str(exe)], input=inputs, capture_output=True, timeout=60, cwd=td)
        except (subprocess.TimeoutExpired, OSError):
            return 0.0
    got = p.stdout.split(b"\n")
    if got and got[-1] == b"":
        got.pop()
    hits = sum(1 for i, e in enumerate(expected) if i < len(got) and got[i] == e)
    return hits / max(len(expected), len(got))
