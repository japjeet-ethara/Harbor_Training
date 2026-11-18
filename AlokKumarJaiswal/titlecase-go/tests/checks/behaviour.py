import sys
from pathlib import Path

from rewardkit import criterion

# Reward Kit loads this file by path and does not put the directory on sys.path.
_CHECKS = Path(__file__).resolve().parent
if str(_CHECKS) not in sys.path:
    sys.path.insert(0, str(_CHECKS))

from _rules import build_binary, rules_ok, run_jailed

_HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
_HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _byte_lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n")


@criterion
def hidden_output_matches(workspace: Path) -> float:
    if not build_binary(workspace):
        return 0.0
    if not rules_ok(workspace):
        return 0.0
    stdout = run_jailed(_HIDDEN_INPUTS.read_bytes())
    if stdout is None or not stdout.endswith(b"\n"):
        return 0.0

    output_lines = stdout[:-1].split(b"\n")
    expected_lines = _byte_lines(_HIDDEN_EXPECTED.read_bytes())
    total = max(len(output_lines), len(expected_lines))
    equal = sum(a == b for a, b in zip(output_lines, expected_lines))
    return equal / total
