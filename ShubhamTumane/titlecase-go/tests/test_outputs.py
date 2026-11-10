import os
import subprocess
import pytest

REPO_DIR = "/workspace/repo"
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def run_cmd(cmd, cwd=REPO_DIR):
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)


def test_build():
    """Build must succeed inside the repository."""
    success, stdout, stderr = run_cmd("go build ./...")
    assert success, f"Go build failed:\nStdout: {stdout}\nStderr: {stderr}"


def test_no_python():
    """No python implementation files should remain in the project."""
    py_files = []
    for root, _, files in os.walk(REPO_DIR):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    assert len(py_files) == 0, f"Found python files in repo: {py_files}"


def test_behaviour():
    """Check line-by-line output against hidden expected dataset."""
    bin_path = "/tmp/titlecase_bin"
    build_ok, stdout, stderr = run_cmd(f"go build -o {bin_path} .", cwd=REPO_DIR)
    assert build_ok and os.path.exists(bin_path), f"Failed to build binary:\n{stderr}"

    hidden_in = os.path.join(TESTS_DIR, "data", "hidden_inputs.txt")
    hidden_exp = os.path.join(TESTS_DIR, "data", "hidden_expected.txt")

    assert os.path.exists(hidden_in), f"Missing {hidden_in}"
    assert os.path.exists(hidden_exp), f"Missing {hidden_exp}"

    with open(hidden_in, "r", encoding="utf-8") as f_in:
        res = subprocess.run(
            [bin_path],
            stdin=f_in,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    assert res.returncode == 0, f"Binary crashed with stderr: {res.stderr}"

    actual_lines = [line.rstrip("\r\n") for line in res.stdout.splitlines()]
    with open(hidden_exp, "r", encoding="utf-8") as f_exp:
        exp_lines = [line.rstrip("\r\n") for line in f_exp.readlines()]

    assert len(actual_lines) == len(exp_lines), (
        f"Output line count mismatch: got {len(actual_lines)}, expected {len(exp_lines)}"
    )

    matches = sum(1 for a, b in zip(actual_lines, exp_lines) if a == b)
    accuracy = matches / len(exp_lines)
    assert accuracy == 1.0, f"Behavior mismatch: only {matches}/{len(exp_lines)} matched."