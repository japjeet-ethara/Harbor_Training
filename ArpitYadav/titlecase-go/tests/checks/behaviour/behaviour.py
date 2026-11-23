#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def check_behaviour():
    repo = Path("/workspace/repo")
    if not repo.exists():
        repo = Path(__file__).resolve().parent.parent.parent.parent

    bin_name = "titlecase_test_bin.exe" if sys.platform == "win32" else "titlecase_test_bin"
    bin_path = repo / bin_name
    build_cmd = ["go", "build", "-o", str(bin_path), "."]
    proc = subprocess.run(build_cmd, cwd=str(repo), capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        print(f"Failed to build Go binary for behaviour check: {proc.stderr}", file=sys.stderr)
        return 0.0

    candidates_inputs = [
        Path("/tests/data/hidden_inputs.txt"),
        repo.parent / "tests" / "data" / "hidden_inputs.txt",
        Path(__file__).resolve().parent.parent.parent / "data" / "hidden_inputs.txt",
    ]
    candidates_expected = [
        Path("/tests/data/hidden_expected.txt"),
        repo.parent / "tests" / "data" / "hidden_expected.txt",
        Path(__file__).resolve().parent.parent.parent / "data" / "hidden_expected.txt",
    ]

    hidden_inputs_path = next((p for p in candidates_inputs if p.exists()), None)
    hidden_expected_path = next((p for p in candidates_expected if p.exists()), None)

    if not hidden_inputs_path or not hidden_expected_path:
        print("Missing hidden test data files!", file=sys.stderr)
        if bin_path.exists():
            bin_path.unlink()
        return 0.0

    input_bytes = hidden_inputs_path.read_bytes()
    expected_bytes = hidden_expected_path.read_bytes()

    try:
        run_proc = subprocess.run(
            [str(bin_path)],
            input=input_bytes,
            capture_output=True,
            cwd=str(repo),
            timeout=120
        )
    finally:
        if bin_path.exists():
            bin_path.unlink()

    if run_proc.returncode != 0:
        print(f"Runtime failure: {run_proc.stderr}", file=sys.stderr)
        return 0.0

    actual_lines = [l.rstrip(b"\r") for l in run_proc.stdout.split(b"\n")]
    expected_lines = [l.rstrip(b"\r") for l in expected_bytes.split(b"\n")]

    if actual_lines and actual_lines[-1] == b"":
        actual_lines.pop()
    if expected_lines and expected_lines[-1] == b"":
        expected_lines.pop()

    if not expected_lines:
        return 0.0

    matches = 0
    total = len(expected_lines)
    for i, exp in enumerate(expected_lines):
        if i < len(actual_lines) and actual_lines[i] == exp:
            matches += 1

    score = matches / total
    print(f"Behaviour check: {matches}/{total} matches ({score:.4%})", file=sys.stderr)
    return score

if __name__ == "__main__":
    score = check_behaviour()
    print(score)
    sys.exit(0 if score == 1.0 else 1)
