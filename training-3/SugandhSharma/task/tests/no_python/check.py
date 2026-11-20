"""Check 2, weight 1: the repository is a REAL port, not just a build.

It pays 1 only when all three hold:
  - no .py file is left anywhere in the repository,
  - the Go build passes, and
  - the program is right on nearly all the hidden titles (at least 90%).

The last clause closes two cheat classes at once. Without it, `no_python` was gated on the build alone, so a
program that compiles, deletes the Python and ports nothing collected this point for free. A partial port that
ports only some rules (small words and apostrophes, say, but not the rest) still passed a lower gate and, worse,
kept the weight-4 behaviour term, scoring about 0.58 as a cheat. The companion hardening is in `tests/gen.py`,
which drops titles the original leaves unchanged, so the hidden set holds only titles that need real work. With
the 90% gate a non-port or a partial port fails here (no_python 0), and `tests/behaviour/check.py` gates its
behaviour to 0 as well, so it scores (build 1 + no_python 0 + behaviour 0) / 6 = 0.1667, below 0.2, while the
oracle and any essentially complete port keep this point. The 90% line sits far above every non-port and
partial cheat (the strongest partial cheat seen reaches about 0.37) and at or below a real port (oracle is 100%).
"""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {"GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}
DATA = Path(__file__).resolve().parent.parent / "data"
REAL_PORT_MIN = 0.90  # an essentially complete port clears this; a non-port or partial port does not


def hidden_share_correct(workspace: Path) -> float:
    """Build the root program, run it on the hidden inputs, return the share of exactly-right lines."""
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    with tempfile.TemporaryDirectory() as tmp:
        program = Path(tmp) / "titlecase"
        try:
            built = subprocess.run(["go", "build", "-o", str(program), "."], cwd=workspace,
                                   env={**os.environ, **GO_ENV}, capture_output=True, timeout=300)
            if built.returncode != 0 or not program.is_file():
                return 0.0
            with open(DATA / "hidden_inputs.txt", "rb") as titles:
                ran = subprocess.run([str(program)], stdin=titles, capture_output=True, timeout=120, cwd=tmp)
        except (OSError, subprocess.TimeoutExpired):
            return 0.0
    got = ran.stdout.split(b"\n")
    right = sum(1 for i, line in enumerate(expected) if i < len(got) and got[i] == line)
    return right / len(expected)


@criterion(description="no .py file is left, the build passes, and the port is right on >=90% of hidden titles")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    for _root, _dirs, files in os.walk(workspace):
        if any(name.lower().endswith(".py") for name in files):
            return False
    if not (workspace / "go.mod").is_file():
        return False
    return hidden_share_correct(workspace) >= REAL_PORT_MIN
