"""Check 2, weight 1: the repository is a REAL port, not just a build.

It pays 1 only when all three hold:
  - no .py file is left anywhere in the repository,
  - the Go build passes, and
  - the program is right on at least a quarter of the hidden titles.

The last clause is one of two hardenings that work together. Without it, `no_python` was gated on the build
alone, so a program that compiles, deletes the Python and ports nothing collected this point for free:
(build 1 + no_python 1 + behaviour) / 6, above the 0.2 cheat bar. The second hardening is in `tests/gen.py`,
which drops titles the original leaves unchanged, so the hidden set now contains only titles that need real
work and a program that merely echoes its input is right on 0% of them. Together, such a non-port fails the
25% gate (no_python 0) and earns no behaviour, so it scores (build 1 + no_python 0 + behaviour 0) / 6 = 0.1667,
below 0.2, while the oracle (behaviour 1.0) and any working port keep this point. The 25% line sits well above
any non-port and well below any real attempt (the oracle is 100%, broken ports in the mutation tests 50%+).
"""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {"GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}
DATA = Path(__file__).resolve().parent.parent / "data"
REAL_PORT_MIN = 0.25  # share of hidden titles a real port clears and a non-port does not


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


@criterion(description="no .py file is left, the build passes, and the port is right on >=25% of hidden titles")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    for _root, _dirs, files in os.walk(workspace):
        if any(name.lower().endswith(".py") for name in files):
            return False
    if not (workspace / "go.mod").is_file():
        return False
    return hidden_share_correct(workspace) >= REAL_PORT_MIN
