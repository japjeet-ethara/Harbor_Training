"""behaviour: fraction of hidden lines that match byte for byte."""

import subprocess
from pathlib import Path

from rewardkit.session import criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
BINARY = Path("/tmp/titlecase-bin")


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion(description="Share of hidden lines that match the original titlecase output")
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    try:
        build = subprocess.run(
            ["go", "build", "-o", str(BINARY), "."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if build.returncode != 0 or not BINARY.is_file():
        return 0.0
    try:
        ran = subprocess.run(
            [str(BINARY)],
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if ran.returncode != 0:
        return 0.0

    expected = _lines(HIDDEN_EXPECTED.read_bytes())
    actual = _lines(ran.stdout)
    total = max(len(expected), len(actual))
    if total == 0:
        return 0.0
    matched = sum(
        1
        for index in range(total)
        if index < len(expected)
        and index < len(actual)
        and expected[index] == actual[index]
    )
    return matched / total
