"""Line-by-line match against the hidden titlecase fixtures."""

import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


@criterion
def behaviour(workspace: Path) -> float:
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return 0.0
    expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
    if not expected:
        return 0.0
    inputs_bytes = HIDDEN_INPUTS.read_bytes()
    os.chmod("/tests/data", 0o700)
    with tempfile.TemporaryDirectory() as tmp:
        os.chmod(tmp, 0o755)
        binary = Path(tmp) / "titlecase"
        built = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
        )
        if built.returncode != 0 or not binary.is_file():
            return 0.0
        os.chmod(binary, 0o755)
        ran = subprocess.run(
            [str(binary)],
            cwd=tmp,
            input=inputs_bytes,
            capture_output=True,
            env={},
            user=65534,
            group=65534,
            timeout=180,
        )
    actual = ran.stdout.decode("utf-8", errors="replace").splitlines()
    matches = sum(
        index < len(actual) and actual[index] == line
        for index, line in enumerate(expected)
    )
    return matches / len(expected)
