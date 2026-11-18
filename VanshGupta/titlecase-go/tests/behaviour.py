import sys
import tempfile
from pathlib import Path

from rewardkit import Worker, WorkerError, criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _go

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _share(expected: str, observed: str) -> float:
    expected_lines = expected.splitlines()
    observed_lines = observed.splitlines()
    if not expected_lines:
        return 0.0
    matches = sum(
        1
        for index, line in enumerate(expected_lines)
        if index < len(observed_lines) and observed_lines[index] == line
    )
    return matches / len(expected_lines)


@criterion
def behaviour(workspace: Path) -> float:
    expected = HIDDEN_EXPECTED.read_text(encoding="utf-8")
    stdin = HIDDEN_INPUTS.read_bytes()
    with tempfile.TemporaryDirectory(prefix="titlecase-bin-") as tmp:
        binary = Path(tmp) / "titlecase"
        if not _go.build_program(workspace, binary):
            return 0.0
        try:
            result = Worker().run(
                "./titlecase",
                files=[binary],
                stdin=stdin,
                timeout_sec=120,
            )
        except WorkerError:
            return 0.0
    try:
        observed = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return 0.0
    return _share(expected, observed)
