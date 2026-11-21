import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion


DATA_DIR = Path(__file__).resolve().parent / "data"


def build_program(
    workspace: Path, binary: Path, package_pattern: str
) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["go", "build", "-o", str(binary), package_pattern],
            cwd=workspace,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    return result.returncode == 0, result.stderr.decode("utf-8", errors="replace")


@criterion(description="Go build ./... succeeds")
def build(workspace: Path, package_pattern: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="titlecase-go-build-") as directory:
        passed, detail = build_program(
            workspace, Path(directory) / "titlecase-go", package_pattern
        )
    if not passed:
        print(detail)
    return passed


@criterion(description="No Python files remain and Go build succeeds")
def no_python(workspace: Path, package_pattern: str) -> bool:
    has_python = any(workspace.rglob("*.py"))
    with tempfile.TemporaryDirectory(prefix="titlecase-go-build-") as directory:
        passed, detail = build_program(
            workspace, Path(directory) / "titlecase-go", package_pattern
        )
    if not passed:
        print(detail)
    return not has_python and passed


@criterion(description="Hidden input/output line match")
def behaviour(workspace: Path, package_pattern: str) -> float:
    with tempfile.TemporaryDirectory(prefix="titlecase-go-build-") as directory:
        binary = Path(directory) / "titlecase-go"
        passed, detail = build_program(workspace, binary, package_pattern)
        if not passed:
            print(detail)
            return 0.0

        inputs = (DATA_DIR / "hidden_inputs.txt").read_bytes()
        expected = (DATA_DIR / "hidden_expected.txt").read_bytes().splitlines()
        try:
            result = subprocess.run(
                [str(binary)],
                cwd=workspace,
                input=inputs,
                capture_output=True,
                timeout=60,
                check=False,
            )
            actual = result.stdout.splitlines()
        except subprocess.TimeoutExpired as error:
            output = error.stdout or b""
            actual = output.splitlines()

    if not expected:
        return 0.0
    correct = sum(
        index < len(actual) and actual[index] == line
        for index, line in enumerate(expected)
    )
    return correct / len(expected)


rk.build(package_pattern="./...", weight=1.0)
rk.no_python(package_pattern="./...", weight=1.0)
rk.behaviour(package_pattern="./...", weight=4.0)
