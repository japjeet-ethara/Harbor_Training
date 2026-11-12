from pathlib import Path
import subprocess
from rewardkit import criterion

DATA_DIR = Path("/tests/data")
BIN_PATH = Path("/tmp/titlecase_verifier_bin")


@criterion(description="fraction of hidden inputs matching Python titlecase() byte-for-byte")
def hidden_behaviour_match(workspace: Path) -> float:
    build = subprocess.run(
        ["go", "build", "-o", str(BIN_PATH), "."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if build.returncode != 0:
        return 0.0

    inputs_bytes = (DATA_DIR / "hidden_inputs.txt").read_bytes()
    expected_lines = (DATA_DIR / "hidden_expected.txt").read_bytes().splitlines()
    if not expected_lines:
        return 0.0

    run = subprocess.run(
        [str(BIN_PATH)],
        cwd=workspace,
        input=inputs_bytes,
        capture_output=True,
        timeout=120,
    )
    if run.returncode != 0:
        return 0.0

    actual_lines = run.stdout.splitlines()
    matches = sum(
        1 for exp, act in zip(expected_lines, actual_lines) if exp == act
    )
    denom = max(len(expected_lines), len(actual_lines))
    return matches / denom
