#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} REPO_DIR TEST_DATA_DIR", file=sys.stderr)
        return 2

    repo_path = Path(sys.argv[1])
    data_path = Path(sys.argv[2])
    input_path = data_path / "inputs.txt"
    expected_path = data_path / "expected.txt"

    with input_path.open(encoding="utf-8") as input_file:
        original_lines = [line.rstrip("\r\n") for line in input_file]
    with expected_path.open(encoding="utf-8") as expected_file:
        expected_lines = [line.rstrip("\r\n") for line in expected_file]

    with tempfile.TemporaryDirectory() as tmpdir:
        bin_path = os.path.join(tmpdir, "titlecase_app.exe")
        build_res = subprocess.run(
            ["go", "build", "-o", bin_path, "."],
            cwd=str(repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if build_res.returncode != 0:
            print(build_res.stdout, end="", file=sys.stderr)
            print(build_res.stderr, end="", file=sys.stderr)
            return build_res.returncode

        with input_path.open(encoding="utf-8") as input_file:
            run_res = subprocess.run(
                [bin_path],
                stdin=input_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
        if run_res.returncode != 0:
            print(run_res.stderr, end="", file=sys.stderr)
            return run_res.returncode
        actual_lines = [line.rstrip("\r\n") for line in run_res.stdout.splitlines()]

    mismatches = []
    mismatch_count = 0
    for index in range(max(len(expected_lines), len(actual_lines))):
        expected = expected_lines[index] if index < len(expected_lines) else "<missing>"
        actual = actual_lines[index] if index < len(actual_lines) else "<missing>"
        if expected != actual:
            mismatch_count += 1
            if len(mismatches) < 10:
                original = original_lines[index] if index < len(original_lines) else "<missing>"
                mismatches.append((index + 1, original, expected, actual))

    for line_number, original, expected, actual in mismatches:
        print(f"Line {line_number}:")
        print(f"  Input:    {original}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
    print(f"Total mismatches: {mismatch_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
