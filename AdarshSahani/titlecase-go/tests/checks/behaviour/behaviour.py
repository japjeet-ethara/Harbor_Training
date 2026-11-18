"""Score the fraction of hidden input lines matching the reference bytes."""

import subprocess
from pathlib import Path

from rewardkit.session import criterion


HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
BINARY = Path("/tmp/titlecase-verifier")


def _lines(data: bytes) -> list[bytes]:
    """Split LF-delimited records while preserving blank records."""
    if data == b"":
        return []
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


@criterion(description="Fraction of hidden title lines matching byte for byte")
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0

    try:
        input_bytes = HIDDEN_INPUTS.read_bytes()
        expected_bytes = HIDDEN_EXPECTED.read_bytes()
    except OSError:
        return 0.0

    inputs = _lines(input_bytes)
    expected = _lines(expected_bytes)
    total = len(inputs)
    if total == 0:
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
        run = subprocess.run(
            [str(BINARY)],
            input=input_bytes,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if run.returncode != 0:
        return 0.0

    actual = _lines(run.stdout)
    matched = sum(
        1
        for index in range(total)
        if index < len(expected)
        and index < len(actual)
        and expected[index] == actual[index]
    )
    return matched / total
