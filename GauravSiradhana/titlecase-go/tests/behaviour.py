"""Share of hidden lines whose Go output matches the frozen Python answer."""

import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
HIDDEN_IN = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXP = Path("/tests/data/hidden_expected.txt")
VISIBLE_EXP = Path("/tests/data/expected.txt")
BINARY = Path("/tmp/titlecase-candidate")


def go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GO111MODULE"] = "on"
    env["GOPROXY"] = "off"
    env["GOSUMDB"] = "off"
    env["GOTOOLCHAIN"] = "local"
    env["CGO_ENABLED"] = "0"
    env["GOCACHE"] = "/tmp/go-build-cache-behaviour"
    env["GOMODCACHE"] = "/tmp/go-mod-cache-behaviour"
    return env


def line_score(stdout: str, expected_text: str) -> float:
    out = stdout.split("\n")
    want = expected_text.split("\n")
    total = max(len(want), 1)
    return sum(1 for actual, expected in zip(out, want) if actual == expected) / total


@criterion
def behaviour(workspace: Path) -> float:
    del workspace
    if not (REPO / "go.mod").is_file():
        return 0.0
    proc = subprocess.run(
        ["go", "build", "-o", str(BINARY), "."],
        cwd=REPO,
        env=go_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0 or not BINARY.is_file():
        return 0.0
    os.chmod(BINARY, 0o755)
    for locked in (HIDDEN_EXP, VISIBLE_EXP):
        if locked.exists():
            os.chmod(locked, 0o600)
    with HIDDEN_IN.open(encoding="utf-8", newline="\n") as stdin:
        run = subprocess.run(
            ["su", "nobody", "-s", "/bin/sh", "-c", str(BINARY)],
            stdin=stdin,
            capture_output=True,
            text=True,
            timeout=120,
        )
    expected = HIDDEN_EXP.read_text(encoding="utf-8")
    return line_score(run.stdout, expected)
