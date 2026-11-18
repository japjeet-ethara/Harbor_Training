from pathlib import Path
import subprocess
from rewardkit import criterion

@criterion
def hidden_behavior_matches(workspace: Path) -> float:
    binary = Path("/tmp/titlecase-hidden-check")
    build = subprocess.run(
        ["go", "build", "-o", str(binary), "."],
        cwd=workspace, capture_output=True, timeout=120
    )
    if build.returncode != 0:
        return 0.0

    data = Path("/tests/data")
    inputs = (data / "hidden_inputs.txt").read_bytes()
    expected = (data / "hidden_expected.txt").read_bytes()

    result = subprocess.run(
        [str(binary)], input=inputs, capture_output=True, timeout=120
    )
    if result.returncode != 0:
        return 0.0

    actual_lines = result.stdout.splitlines()
    expected_lines = expected.splitlines()
    if not expected_lines:
        return 0.0

    matches = sum(
        1 for a, e in zip(actual_lines, expected_lines) if a == e
    )
    return matches / len(expected_lines)

