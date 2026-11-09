import subprocess
from pathlib import Path

from rewardkit.session import criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion(description="Share of hidden lines matching hidden_expected.txt")
def behaviour(workspace: Path) -> float:
    if not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    binary = Path("/tmp/titlecase-go-behaviour")
    try:
        build = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if build.returncode != 0:
        return 0.0
    try:
        proc = subprocess.run(
            [str(binary)],
            cwd=workspace,
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if proc.returncode != 0:
        return 0.0
    expected = _lines(HIDDEN_EXPECTED.read_bytes())
    actual = _lines(proc.stdout)
    if not expected:
        return 0.0
    matches = sum(
        1 for index, line in enumerate(expected) if index < len(actual) and actual[index] == line
    )
    return matches / len(expected)
