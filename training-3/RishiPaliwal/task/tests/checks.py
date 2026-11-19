import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


DATA_DIR = Path(__file__).resolve().parent / "data"


def _build_all(workspace):
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _build_program(workspace, output):
    try:
        result = subprocess.run(
            ["go", "build", "-o", str(output), "."],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _build_check(workspace):
    return _build_all(workspace)


def _no_python_check(workspace):
    has_python = any(
        path.is_file() and path.suffix.lower() == ".py"
        for path in workspace.rglob("*")
    )
    return not has_python and _build_all(workspace)


def _behaviour_check(workspace):
    inputs = (DATA_DIR / "hidden_inputs.txt").read_bytes()
    expected = (DATA_DIR / "hidden_expected.txt").read_bytes().splitlines()

    with tempfile.TemporaryDirectory(prefix="titlecase-go-") as temp_dir:
        executable = Path(temp_dir) / "titlecase"
        if not _build_program(workspace, executable):
            return 0.0
        try:
            result = subprocess.run(
                [str(executable)],
                cwd=workspace,
                input=inputs,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=180,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return 0.0

    actual = result.stdout.splitlines()
    matched = sum(left == right for left, right in zip(actual, expected))
    line_count = max(len(actual), len(expected))
    return matched / line_count if line_count else 1.0


@criterion(description="{check_name} check", shared=True)
def check(workspace: Path, check_name: str):
    if check_name == "build":
        return _build_check(workspace)
    if check_name == "no_python":
        return _no_python_check(workspace)
    if check_name == "behaviour":
        return _behaviour_check(workspace)
    raise ValueError(f"Unknown check: {check_name}")
