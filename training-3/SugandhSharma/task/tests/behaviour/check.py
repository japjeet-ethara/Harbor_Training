"""Check 3, weight 4: share of the HIDDEN titles for which the Go program prints exactly the frozen answer."""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {"GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}
DATA = Path(__file__).resolve().parent.parent / "data"


@criterion(description="share of hidden titles whose output equals the original Python titlecase()")
def behaviour(workspace: Path) -> float:
    if not (workspace / "go.mod").is_file():
        return 0.0
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
