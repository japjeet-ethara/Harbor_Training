import os
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
BINARY = Path("/tmp/tc")
HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
RUN_TIMEOUT_SEC = 120


def _lines(data: bytes) -> list[bytes]:
    if not data:
        return []
    lines: list[bytes] = []
    start = 0
    for index, byte in enumerate(data):
        if byte == 0x0A:
            lines.append(data[start : index + 1])
            start = index + 1
    if start < len(data):
        lines.append(data[start:])
    return lines


def _line_score(actual: bytes, expected: bytes) -> float:
    actual_lines = _lines(actual)
    expected_lines = _lines(expected)
    total = len(expected_lines)
    if total == 0:
        return 0.0
    matches = sum(
        1
        for index, line in enumerate(expected_lines)
        if index < len(actual_lines) and actual_lines[index] == line
    )
    extra = len(actual_lines) - total
    if extra > 0:
        matches -= extra
    if matches < 0:
        matches = 0
    return matches / total


@criterion
def behaviour(workspace: Path) -> float:
    del workspace
    try:
        env = os.environ.copy()
        env["GOPROXY"] = "off"
        env["GOFLAGS"] = "-mod=readonly"
        build = subprocess.run(
            ["go", "build", "-o", str(BINARY), "."],
            cwd=REPO,
            env=env,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if build.returncode != 0:
        return 0.0
    try:
        stdin = HIDDEN_INPUTS.read_bytes()
        expected = HIDDEN_EXPECTED.read_bytes()
    except OSError:
        return 0.0
    try:
        run = subprocess.run(
            [str(BINARY)],
            input=stdin,
            capture_output=True,
            timeout=RUN_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if run.returncode != 0:
        return 0.0
    return _line_score(run.stdout, expected)
