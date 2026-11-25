import os
import stat
import subprocess
from pathlib import Path

from rewardkit.session import criterion

HIDDEN_INPUTS = Path("/tests/data/inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/answers.txt")


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


def _hide_files(paths: tuple[Path, ...]) -> list[tuple[Path, bytes, int]]:
    saved: list[tuple[Path, bytes, int]] = []
    try:
        for path in paths:
            data = path.read_bytes()
            mode = stat.S_IMODE(path.stat().st_mode)
            path.unlink()
            saved.append((path, data, mode))
        return saved
    except OSError:
        _restore_files(saved)
        raise


def _restore_files(saved: list[tuple[Path, bytes, int]]) -> None:
    for path, data, mode in saved:
        path.write_bytes(data)
        path.chmod(mode)


@criterion(description="Share of hidden lines matching verifier-held answers")
def behaviour(workspace: Path) -> float:
    try:
        hidden_inputs = HIDDEN_INPUTS.read_bytes()
        expected_data = HIDDEN_EXPECTED.read_bytes()
    except OSError:
        return 0.0

    expected = _lines(expected_data)
    if not expected:
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

    saved: list[tuple[Path, bytes, int]] = []
    try:
        # Keep the answer key and fixed test list in verifier memory while the
        # contestant executable runs. The executable must not be able to read
        # these files from the shared verifier filesystem.
        saved = _hide_files((HIDDEN_INPUTS, HIDDEN_EXPECTED))
        proc = subprocess.run(
            [str(binary)],
            cwd=workspace,
            input=hidden_inputs,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    finally:
        if saved:
            _restore_files(saved)

    if proc.returncode != 0:
        return 0.0
    actual = _lines(proc.stdout)
    matches = sum(
        1 for index, line in enumerate(expected) if index < len(actual) and actual[index] == line
    )
    return matches / len(expected)