from pathlib import Path
import subprocess

from rewardkit import criterion

INPUTS = Path("/tests/data/hidden_inputs.txt")
EXPECTED = Path("/tests/data/hidden_expected.txt")
BINARY = Path("/tmp/titlecase-go")


@criterion
def hidden_behaviour_matches(workspace: Path) -> float:
    build = subprocess.run(
        ["go", "build", "-o", str(BINARY), "."],
        cwd=workspace,
        capture_output=True,
        timeout=120,
    )

    if build.returncode != 0:
        return 0.0

    result = subprocess.run(
        [str(BINARY)],
        input=INPUTS.read_bytes(),
        capture_output=True,
        timeout=120,
    )

    if result.returncode != 0:
        return 0.0

    actual = result.stdout.splitlines()
    expected = EXPECTED.read_bytes().splitlines()

    if not expected or len(actual) != len(expected):
        return 0.0

    matches = sum(
        a == e for a, e in zip(actual, expected)
    )

    return matches / len(expected)
