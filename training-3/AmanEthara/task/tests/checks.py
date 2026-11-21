import subprocess
from pathlib import Path
import rewardkit as rk


@rk.criterion(description="go build ./... succeeds")
def build(workspace: Path) -> float:
    try:
        proc = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        return 1.0 if proc.returncode == 0 else 0.0
    except Exception:
        return 0.0


@rk.criterion(description="no .py files anywhere under workspace AND go build succeeds")
def no_python(workspace: Path) -> float:
    # First: go build ./... must succeed
    try:
        proc = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return 0.0
    except Exception:
        return 0.0

    # Second: no .py files anywhere under workspace
    py_files = list(workspace.rglob("*.py"))
    return 1.0 if len(py_files) == 0 else 0.0


@rk.criterion(description="proportion of output lines exactly matching hidden_expected.txt")
def behaviour(workspace: Path) -> float:
    bin_path = "/tmp/titlecase_bin"
    # Build executable in workspace
    try:
        proc = subprocess.run(
            ["go", "build", "-o", bin_path, "."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return 0.0
    except Exception:
        return 0.0

    # Read hidden inputs and hidden expected outputs
    inputs_file = Path("/tests/data/hidden_inputs.txt")
    expected_file = Path("/tests/data/hidden_expected.txt")
    if not inputs_file.exists():
        inputs_file = Path(__file__).parent / "data" / "hidden_inputs.txt"
        expected_file = Path(__file__).parent / "data" / "hidden_expected.txt"

    if not inputs_file.exists() or not expected_file.exists():
        return 0.0

    try:
        with open(inputs_file, "rb") as f_in:
            run_proc = subprocess.run(
                [bin_path],
                input=f_in.read(),
                capture_output=True,
                timeout=120,
            )
        if run_proc.returncode != 0:
            return 0.0

        actual_lines = run_proc.stdout.decode("utf-8", errors="replace").splitlines()
        with open(expected_file, "r", encoding="utf-8") as f_exp:
            expected_lines = f_exp.read().splitlines()

        if not expected_lines:
            return 0.0

        matches = sum(1 for act, exp in zip(actual_lines, expected_lines) if act == exp)
        return matches / len(expected_lines)
    except Exception:
        return 0.0


# Register criteria with their exact weights:
rk.build(weight=1.0)
rk.no_python(weight=1.0)
rk.behaviour(weight=4.0)
