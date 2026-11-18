import subprocess
import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from go_build_util import go_build

DATA = Path(__file__).resolve().parents[1] / "data"
HIDDEN_INPUTS = DATA / "hidden_inputs.txt"
HIDDEN_EXPECTED = DATA / "hidden_expected.txt"


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion
def behaviour(workspace: Path) -> float:
    """Share of output lines that exactly match the hidden expected titles."""
    if not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    expected = _lines(HIDDEN_EXPECTED.read_bytes())
    if not expected:
        return 0.0

    binary = Path("/tmp/titlecase-behaviour")
    if not go_build(workspace, ["build", "-o", str(binary), "."]):
        return 0.0
    try:
        result = subprocess.run(
            [str(binary)],
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            return 0.0
    except (OSError, subprocess.TimeoutExpired):
        return 0.0

    actual = _lines(result.stdout)
    matches = sum(
        1 for index, line in enumerate(expected) if index < len(actual) and actual[index] == line
    )
    return matches / len(expected)
