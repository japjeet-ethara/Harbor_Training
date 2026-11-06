"""behaviour: share of hidden lines the Go program gets exactly right."""

import os
import signal
import subprocess
from contextlib import suppress
from pathlib import Path

from rewardkit import criterion

DATA = Path("/tests/data")
BINARY = "/tmp/titlecase-port"
TIMEOUT_SEC = 300


def run_program(stdin):
    """Run the program as nobody, which cannot read /tests/data."""
    process = subprocess.Popen(
        [BINARY],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd="/",
        env={},
        user="nobody",
        group="nogroup",
        extra_groups=[],
        start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(stdin, timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        stdout = None
    with suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()
    return stdout


@criterion(description="Share of hidden lines matching the original exactly")
def hidden_lines_match(workspace: Path) -> float:
    try:
        build = subprocess.run(
            ["go", "build", "-o", BINARY, "."],
            cwd=workspace,
            capture_output=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return 0.0
    if build.returncode != 0:
        return 0.0
    os.chmod(BINARY, 0o755)

    stdout = run_program((DATA / "hidden_inputs.txt").read_bytes())
    if stdout is None:
        return 0.0

    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    actual = stdout.split(b"\n")
    unterminated = actual.pop()  # empty when the output ends in a newline
    # Extra lines lower the score. An unterminated last line never matches.
    total = max(len(expected), len(actual) + bool(unterminated))
    matches = sum(want == got for want, got in zip(expected, actual))
    return matches / total
