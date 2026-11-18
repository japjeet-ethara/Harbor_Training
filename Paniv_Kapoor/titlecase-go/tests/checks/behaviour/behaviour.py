"""Score the fraction of hidden titles the Go program title-cases correctly."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

_HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
_HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
_BINARY = Path("/tmp/titlecase-behaviour")
_BUILD_TIMEOUT_SEC = 180
_RUN_TIMEOUT_SEC = 60


def _run_jailed(binary: Path, stdin: bytes) -> subprocess.CompletedProcess[bytes] | None:
    """Run the submission where it cannot read the verifier's files.

    The Go toolchain emits a static binary, so a chroot that contains only that
    binary still lets it read stdin and write stdout.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="titlecase-jail-") as directory:
            jail = Path(directory)
            target = jail / "titlecase"
            shutil.copy(binary, target)
            os.chmod(target, 0o755)
            return subprocess.run(
                ["chroot", str(jail), "/titlecase"],
                input=stdin,
                capture_output=True,
                timeout=_RUN_TIMEOUT_SEC,
            )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion(description="share of output lines matching the hidden expected titles")
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0
    if not _HIDDEN_INPUTS.is_file() or not _HIDDEN_EXPECTED.is_file():
        return 0.0
    try:
        expected = _lines(_HIDDEN_EXPECTED.read_bytes())
    except OSError:
        return 0.0
    if not expected:
        return 0.0

    try:
        built = subprocess.run(
            ["go", "build", "-o", str(_BINARY), "."],
            cwd=workspace,
            capture_output=True,
            timeout=_BUILD_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if built.returncode != 0:
        return 0.0

    try:
        ran = _run_jailed(_BINARY, _HIDDEN_INPUTS.read_bytes())
    except OSError:
        return 0.0
    if ran is None:
        return 0.0

    got = _lines(ran.stdout)
    matched = sum(
        1 for index, line in enumerate(expected) if index < len(got) and got[index] == line
    )
    return matched / len(expected)
