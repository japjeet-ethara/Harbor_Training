"""Check 3 (weight 4): output on the HIDDEN titles.

Score = share of lines that match hidden_expected.txt exactly (byte for byte).
The expected answers were produced by the original Python titlecase() (tools/gen.py).
"""
import os
import subprocess
from pathlib import Path

import rewardkit as rk

DATA = Path("/tests/data")


@rk.criterion(description="share of hidden titles whose output matches the original exactly")
def behaviour(workspace) -> float:
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off",
               GOTOOLCHAIN="local", GOCACHE="/tmp/gocache-behaviour", CGO_ENABLED="0")
    binary = "/tmp/titlecase_bin"
    if os.path.exists(binary):
        os.remove(binary)

    if not (workspace / "go.mod").is_file():
        return 0.0
    try:
        b = subprocess.run(["go", "build", "-o", binary, "."], cwd=workspace, env=env,
                           capture_output=True, timeout=240)
    except (subprocess.TimeoutExpired, OSError):
        return 0.0
    if b.returncode != 0 or not os.path.exists(binary):
        return 0.0

    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]

    try:
        r = subprocess.run([binary], input=inputs, capture_output=True, timeout=120,
                           cwd="/tmp")
    except (subprocess.TimeoutExpired, OSError):
        return 0.0

    got = r.stdout.split(b"\n")
    if got and got[-1] == b"":
        got = got[:-1]
    matches = sum(1 for i, exp in enumerate(expected) if i < len(got) and got[i] == exp)
    return matches / len(expected)
