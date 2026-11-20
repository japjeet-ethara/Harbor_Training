

"""Require an exact match for every hidden title."""

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
    """Run the submission without access to verifier files."""
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


@criterion(description="all hidden titles must match exactly")
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0

    try:
        input_bytes = _HIDDEN_INPUTS.read_bytes().replace(b"\r\n", b"\n")
        expected_bytes = _HIDDEN_EXPECTED.read_bytes().replace(b"\r\n", b"\n")
    except OSError:
        return 0.0

    if not expected_bytes:
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
        print("Go build failed:", built.stderr.decode("utf-8", errors="replace"), flush=True)
        return 0.0

    ran = _run_jailed(_BINARY, input_bytes)

    if ran is None or ran.returncode != 0:
        print("Program execution failed.", flush=True)
        return 0.0

    if ran.stdout != expected_bytes:
        common = min(len(ran.stdout), len(expected_bytes))

        mismatch = next(
            (
                index
                for index, (actual, expected) in enumerate(
                    zip(ran.stdout, expected_bytes)
                )
                if actual != expected
            ),
            common,
        )

        start = max(0, mismatch - 40)
        end = mismatch + 80

        print(f"Actual output length: {len(ran.stdout)}", flush=True)
        print(f"Expected output length: {len(expected_bytes)}", flush=True)
        print(f"First mismatch byte: {mismatch}", flush=True)
        print(f"Actual snippet: {ran.stdout[start:end]!r}", flush=True)
        print(f"Expected snippet: {expected_bytes[start:end]!r}", flush=True)

        # Temporary diagnostic: identify the first mismatching output line.
        line_number = expected_bytes[:mismatch].count(b"\n")

        input_lines = input_bytes.splitlines()
        actual_lines = ran.stdout.splitlines()
        expected_lines = expected_bytes.splitlines()

        print(f"Mismatch output line: {line_number + 1}", flush=True)

        if line_number < len(input_lines):
            print(f"Input line: {input_lines[line_number]!r}", flush=True)

        if line_number < len(actual_lines):
            print(f"Actual line: {actual_lines[line_number]!r}", flush=True)

        if line_number < len(expected_lines):
            print(f"Expected line: {expected_lines[line_number]!r}", flush=True)

        return 0.0

    return 1.0
