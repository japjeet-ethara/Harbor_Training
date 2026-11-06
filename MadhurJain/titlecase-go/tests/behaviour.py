import subprocess
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

_TIMEOUT_SEC = 120
_DATA = Path(__file__).resolve().parent / "data"
_BINARY = "/tmp/titlecase-under-test"


def _line_score(expected: bytes, actual: bytes) -> float:
    expected_lines = expected.split(b"\n")
    actual_lines = actual.split(b"\n")
    if not expected_lines:
        return 0.0
    matched = 0
    for index, line in enumerate(expected_lines):
        if index < len(actual_lines) and actual_lines[index] == line:
            matched += 1
    return matched / len(expected_lines)


@criterion
def behaviour(workspace: Path) -> float:
    expected = (_DATA / "hidden_expected.txt").read_bytes()
    stdin = (_DATA / "hidden_inputs.txt").read_bytes()
    try:
        build = subprocess.run(
            ["go", "build", "-o", _BINARY, "."],
            cwd=workspace,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0.0
    if build.returncode != 0:
        return 0.0
    try:
        run = subprocess.run(
            [_BINARY],
            cwd=workspace,
            input=stdin,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0.0
    return _line_score(expected, run.stdout)


rk.behaviour()
