import os
import subprocess
from pathlib import Path

from rewardkit import criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


@criterion
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0
    has_program = any(
        path.is_file() and path.suffix == ".go" and not path.name.endswith("_test.go")
        for path in workspace.rglob("*")
    )
    if not has_program:
        return 0.0
    expected_lines = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
    if not expected_lines:
        return 0.0

    cache = Path("/tmp/gocache-behaviour")
    binary = Path("/tmp/titlecase-behaviour")
    env = os.environ.copy()
    env["GOCACHE"] = str(cache / "cache")
    env["GOMODCACHE"] = str(cache / "mod")
    build = subprocess.run(
        ["go", "build", "-o", str(binary), "."],
        cwd=workspace,
        env=env,
        capture_output=True,
        timeout=120,
    )
    if build.returncode != 0 or not binary.is_file():
        return 0.0

    run = subprocess.run(
        [str(binary)],
        cwd=workspace,
        input=HIDDEN_INPUTS.read_bytes(),
        capture_output=True,
        timeout=60,
    )
    if run.returncode != 0:
        return 0.0

    actual_lines = run.stdout.decode("utf-8", errors="replace").splitlines()
    matches = sum(
        1
        for index, expected in enumerate(expected_lines)
        if index < len(actual_lines) and actual_lines[index] == expected
    )
    extra = len(actual_lines) - len(expected_lines)
    if extra > 0:
        matches -= extra
    if matches < 0:
        matches = 0
    return matches / len(expected_lines)
