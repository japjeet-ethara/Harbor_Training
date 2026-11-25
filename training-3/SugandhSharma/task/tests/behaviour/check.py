"""Check 3, weight 4: share of the HIDDEN titles for which the Go program prints exactly the frozen answer.

The share is credited only when it clears REAL_PORT_MIN (an essentially complete, byte-exact port). A partial
port that gets some rules right but not others earns 0 here, so it cannot ride the weight-4 term over the 0.2
cheat bar; a non-port earns 0 anyway. The oracle (100% correct) and any near-complete port keep the full score.
This gate is what makes the partial-port cheat (which reaches about 0.37 share) score only the build point.
"""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {"GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}
DATA = Path(__file__).resolve().parent.parent / "data"
REAL_PORT_MIN = 0.90  # credit the share only for an essentially complete port; a partial port scores 0


@criterion(description="share of hidden titles matching Python exactly, credited only for a near-complete (>=90%) port")
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
    share = right / len(expected)
    return share if share >= REAL_PORT_MIN else 0.0
