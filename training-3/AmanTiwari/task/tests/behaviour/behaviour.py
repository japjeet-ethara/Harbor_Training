"""behaviour (the only paid check): share of HIDDEN lines that match exactly.

Gated: returns 0 unless every hard rule passes (build, no_python, no_exec). So a
program that builds but does no real titlecasing, or one that tries to shell out to
Python, scores 0 here and therefore 0 overall (reward = behaviour, see reward.toml).

Builds the Go program, feeds it data/hidden_inputs.txt on stdin as the unprivileged
user `runner`, and compares each output line byte for byte with hidden_expected.txt.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import DATA_DIR, build_binary, gates_pass, run_as_runner  # noqa: E402

import rewardkit as rk  # noqa: E402
from rewardkit import criterion  # noqa: E402


def _lines(data: bytes) -> list[bytes]:
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


@criterion(description="share of hidden titles whose output matches the original byte for byte (0 if any hard rule fails)")
def hidden_lines_match(workspace: Path) -> float:
    if not gates_pass(workspace):
        return 0.0

    inputs = (DATA_DIR / "hidden_inputs.txt").read_bytes()
    expected = _lines((DATA_DIR / "hidden_expected.txt").read_bytes())

    tmp = Path(tempfile.mkdtemp(prefix="tcgo-"))
    try:
        os.chmod(tmp, 0o755)
        binary = tmp / "titlecase"
        if not build_binary(workspace, binary):
            return 0.0
        out = run_as_runner(binary, inputs)
        if out is None:
            return 0.0
        actual = _lines(out)
        correct = sum(1 for i, exp in enumerate(expected)
                      if i < len(actual) and actual[i] == exp)
        return correct / len(expected)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


rk.hidden_lines_match()
