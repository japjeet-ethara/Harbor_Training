import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path(os.environ.get("TITLECASE_REPO", "/workspace/repo"))
HIDDEN_IN = Path(os.environ.get("TITLECASE_HIDDEN_IN", "/tests/data/hidden_inputs.txt"))
HIDDEN_OUT = Path(os.environ.get("TITLECASE_HIDDEN_OUT", "/tests/data/hidden_expected.txt"))
BINARY = Path("/tmp/titlecase-bin")


@criterion
def behaviour(workspace: Path) -> float:
    del workspace
    built = subprocess.run(
        ["go", "build", "-o", str(BINARY), "."],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        return 0.0
    expected = HIDDEN_OUT.read_text(encoding="utf-8").splitlines()
    if not expected:
        return 0.0
    proc = subprocess.run(
        [str(BINARY)],
        input=HIDDEN_IN.read_bytes(),
        capture_output=True,
    )
    actual = proc.stdout.decode("utf-8").splitlines()
    matches = sum(
        1 for index, line in enumerate(expected) if index < len(actual) and actual[index] == line
    )
    return matches / len(expected)
