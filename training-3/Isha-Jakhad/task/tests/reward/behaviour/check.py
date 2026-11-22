"""Score the fraction of exam titles matched by a native Go implementation."""

import os
import pwd
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import build_binary, gates_pass, run_as_runner

from rewardkit import criterion

DATA_DIR = Path("/tests/data")
INPUTS = DATA_DIR / "inputs.txt"
ANSWERS = DATA_DIR / "answers.txt"
RUN_USER = "runner"


def _records(data: bytes) -> list[bytes]:
    records = data.split(b"\n")
    if records and records[-1] == b"":
        records.pop()
    return records


def _load_exam() -> tuple[bytes, list[bytes]] | None:
    """Load answers into the verifier, then remove the on-disk answer sheet."""
    try:
        inputs = INPUTS.read_bytes()
        expected = _records(ANSWERS.read_bytes())
        ANSWERS.unlink()
    except (OSError, UnicodeError):
        return None
    return inputs, expected


@criterion(description="fraction of exam titles that match byte for byte")
def behaviour(workspace: Path) -> float:
    if not gates_pass(workspace):
        return 0.0

    loaded = _load_exam()
    if loaded is None:
        return 0.0
    inputs, expected = loaded

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o755)
        binary = Path(temp_dir) / "titlecase"
        if not build_binary(workspace, binary):
            return 0.0
        try:
            user = pwd.getpwnam(RUN_USER)
        except KeyError:
            return 0.0
        actual = run_as_runner(binary, inputs, user)
        if actual is None:
            return 0.0

    actual_records = _records(actual)
    total = max(len(expected), len(actual_records))
    if total == 0:
        return 1.0
    matched = sum(
        1
        for index, answer in enumerate(expected)
        if index < len(actual_records) and actual_records[index] == answer
    )
    return matched / total
