import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion

from go_run import go

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion
def behaviour(workspace: Path) -> float:
    try:
        expected = lines(HIDDEN_EXPECTED.read_bytes())
        stdin = HIDDEN_INPUTS.read_bytes()
    except OSError:
        return 0.0
    if not expected:
        return 0.0
    result = go(workspace, "go build -o titlecase.bin . && ./titlecase.bin", stdin)
    if result is None:
        return 0.0
    got = lines(result.stdout)
    matched = sum(
        1 for index, wanted in enumerate(expected) if index < len(got) and got[index] == wanted
    )
    return matched / len(expected)
