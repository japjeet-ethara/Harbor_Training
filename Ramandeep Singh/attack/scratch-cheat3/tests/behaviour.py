"""Check 3 (weight 4): build the Go program, feed it the HIDDEN inputs, and score the
share of lines that match the HIDDEN expected output byte for byte.

The expected answers in data/hidden_expected.txt were produced by running the original
Python titlecase() (see gen.py). Nothing in this file or in data/ is visible to the agent.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk

DATA = Path(__file__).resolve().parent / "data"


def _lines(raw: bytes) -> list:
    parts = raw.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


@rk.criterion(description="share of hidden input lines whose output is byte-exact")
def hidden_lines_exact(workspace: Path) -> float:
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = _lines((DATA / "hidden_expected.txt").read_bytes())
    total = len(expected)
    if total == 0 or not workspace.is_dir():
        return 0.0
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off", GOTOOLCHAIN="local",
               GOCACHE="/tmp/go-build-cache-verifier-behaviour", CGO_ENABLED="0")
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "titlecase_prog")
        try:
            b = subprocess.run(["go", "build", "-o", exe, "."], cwd=workspace, env=env,
                               capture_output=True, text=True, timeout=300)
            if b.returncode != 0:
                return 0.0
            r = subprocess.run([exe], cwd=tmp, input=inputs, capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            return 0.0
    actual = _lines(r.stdout)
    good = sum(1 for i in range(total) if i < len(actual) and actual[i] == expected[i])
    return good / total


rk.hidden_lines_exact()
