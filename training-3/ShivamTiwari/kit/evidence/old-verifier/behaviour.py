import importlib.util
from pathlib import Path

from rewardkit import criterion

_spec = importlib.util.spec_from_file_location(
    "titlecase_go_worker", Path(__file__).resolve().parent / "go_worker.py"
)
_worker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker)

DATA = Path(__file__).resolve().parent / "data"


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion
def behaviour(workspace: Path) -> float:
    expected = _lines((DATA / "hidden_expected.txt").read_bytes())
    if not expected:
        return 0.0
    result = _worker.run_go_or_fail(
        workspace,
        "/usr/local/go/bin/go build -o titlecase .",
        stdin=(DATA / "hidden_inputs.txt").read_bytes(),
        run_binary=True,
    )
    if result is None:
        return 0.0
    got = _lines(result.stdout)
    matches = sum(1 for index, line in enumerate(expected) if index < len(got) and got[index] == line)
    return matches / len(expected)
