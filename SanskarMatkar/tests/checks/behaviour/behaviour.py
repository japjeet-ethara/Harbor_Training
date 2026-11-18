"""behaviour (weight 4): build the Go program, feed it the HIDDEN inputs and
score = share of output lines that exactly match the frozen Python answers.

Only tests/data/hidden_*.txt is used here. The visible inputs.txt /
expected.txt are for the task author's debugging and are never graded, so a
program that memorises them scores ~0 on this check.
"""
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk

DATA = Path(__file__).resolve().parents[2] / "data"   # /tests/data


def _lines(raw: bytes) -> list[bytes]:
    parts = raw.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


@rk.criterion(description="Share of hidden titles whose output matches Python byte for byte")
def hidden_output_matches(workspace: Path) -> float:
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = _lines((DATA / "hidden_expected.txt").read_bytes())
    if not (workspace / "go.mod").is_file():
        print("no go.mod")
        return 0.0
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "titlecase"
        try:
            b = subprocess.run(["go", "build", "-o", str(exe), "."], cwd=workspace,
                               capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            print("build timed out")
            return 0.0
        if b.returncode != 0 or not exe.exists():
            print("build of root package failed:\n" + b.stderr[-2000:])
            return 0.0
        try:
            r = subprocess.run([str(exe)], input=inputs, capture_output=True,
                               timeout=120, cwd=tmp)
        except subprocess.TimeoutExpired:
            print("program timed out")
            return 0.0
    got = _lines(r.stdout)
    ok = sum(1 for i, want in enumerate(expected) if i < len(got) and got[i] == want)
    if len(got) != len(expected):
        print(f"line count mismatch: got {len(got)}, expected {len(expected)}")
    print(f"matched {ok}/{len(expected)} hidden lines")
    return ok / len(expected)
