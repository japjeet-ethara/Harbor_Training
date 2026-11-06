"""Score the share of hidden lines that match the original titlecase output."""

import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOCACHE"] = tempfile.mkdtemp(prefix="go-cache-")
    env["CGO_ENABLED"] = "0"
    env["GOTOOLCHAIN"] = "local"
    return env


@criterion
def behaviour(workspace: Path) -> float:
    del workspace
    if not REPO.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
    if not expected:
        return 0.0
    binary = Path(tempfile.mkdtemp(prefix="titlecase-")) / "titlecase"
    try:
        build = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=REPO,
            env=_go_env(),
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if build.returncode != 0 or not binary.is_file():
        return 0.0
    try:
        run = subprocess.run(
            [str(binary)],
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    try:
        got = run.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return 0.0
    matches = sum(1 for i, line in enumerate(expected) if i < len(got) and got[i] == line)
    return matches / len(expected)
