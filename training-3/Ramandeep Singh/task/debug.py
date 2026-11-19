#!/usr/bin/env python3
"""
Debug script: Compares the Go implementation against tests/data/inputs.txt
and tests/data/expected.txt.

Prints the first 10 mismatches showing:
1. Original input
2. Expected Python output
3. Actual Go output
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_or_extract_go_code(base_dir: Path, custom_source: str = None) -> tuple[Path, bool]:
    """
    Returns (path_to_go_code, is_temporary).
    If custom_source is provided, uses that directory.
    Otherwise checks:
      1. /workspace/repo (container environment)
      2. solution/solve.sh (extracts fresh main.go & go.mod)
      3. jobs/**/artifacts/workspace/repo (recent trial artifacts)
    """
    if custom_source:
        p = Path(custom_source).resolve()
        if (p / "main.go").is_file():
            return p, False
        raise FileNotFoundError(f"No main.go found in custom source: {p}")

    # 1. Container workspace path
    container_ws = Path("/workspace/repo")
    if (container_ws / "main.go").is_file():
        return container_ws, False

    # 2. Extract directly from solution/solve.sh (canonical source)
    solve_sh = base_dir / "solution" / "solve.sh"
    if solve_sh.is_file():
        content = solve_sh.read_text(encoding="utf-8")
        main_go_match = re.search(r"cat > main\.go << 'GOEOF'\n(.*?)\nGOEOF", content, re.DOTALL)
        if main_go_match:
            temp_dir = Path(tempfile.mkdtemp(prefix="titlecase_go_src_"))
            go_mod_match = re.search(r"cat > go\.mod << 'EOF'\n(.*?)\nEOF", content, re.DOTALL)
            if go_mod_match:
                (temp_dir / "go.mod").write_text(go_mod_match.group(1), encoding="utf-8")
            else:
                (temp_dir / "go.mod").write_text("module titlecase\n\ngo 1.23\n", encoding="utf-8")
            (temp_dir / "main.go").write_text(main_go_match.group(1), encoding="utf-8")
            return temp_dir, True

    # 3. Check artifacts from recent job runs
    artifacts = list(base_dir.glob("jobs/**/artifacts/workspace/repo/main.go"))
    if artifacts:
        return artifacts[-1].parent, False

    # 4. Check if main.go exists in base directory
    if (base_dir / "main.go").is_file():
        return base_dir, False

    raise RuntimeError("Could not find or extract the Go implementation.")


def main():
    parser = argparse.ArgumentParser(
        description="Run Go titlecase implementation against visible dataset and compare outputs."
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional path to a directory containing main.go and go.mod.",
    )
    parser.add_argument(
        "--inputs",
        type=str,
        default=None,
        help="Path to inputs file (defaults to tests/data/inputs.txt).",
    )
    parser.add_argument(
        "--expected",
        type=str,
        default=None,
        help="Path to expected outputs file (defaults to tests/data/expected.txt).",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent

    inputs_path = Path(args.inputs) if args.inputs else base_dir / "tests" / "data" / "inputs.txt"
    expected_path = Path(args.expected) if args.expected else base_dir / "tests" / "data" / "expected.txt"

    if not inputs_path.is_file():
        print(f"Error: inputs file not found at {inputs_path}", file=sys.stderr)
        sys.exit(1)
    if not expected_path.is_file():
        print(f"Error: expected file not found at {expected_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading inputs from   : {inputs_path}")
    print(f"Loading expected from : {expected_path}")

    with open(inputs_path, "r", encoding="utf-8") as f:
        inputs = f.read().splitlines()

    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().splitlines()

    if len(inputs) != len(expected):
        print(
            f"Warning: line count mismatch: {len(inputs)} inputs vs {len(expected)} expected lines.",
            file=sys.stderr,
        )

    # Locate or extract Go source
    go_src_dir, is_temp_src = find_or_extract_go_code(base_dir, custom_source=args.source)
    print(f"Using Go source from  : {go_src_dir} (temporary={is_temp_src})")

    # Build Go binary to a temporary executable
    temp_bin_dir = Path(tempfile.mkdtemp(prefix="titlecase_bin_"))
    bin_name = "titlecase_debug.exe" if sys.platform == "win32" else "titlecase_debug"
    bin_path = temp_bin_dir / bin_name

    env = os.environ.copy()
    if "GOCACHE" not in env:
        env["GOCACHE"] = str(Path(tempfile.gettempdir()) / "gocache")

    print("Building Go binary...")
    build_cmd = ["go", "build", "-o", str(bin_path), "."]
    build_res = subprocess.run(
        build_cmd,
        cwd=str(go_src_dir),
        capture_output=True,
        text=True,
        env=env,
    )

    if build_res.returncode != 0:
        print("Go build failed!", file=sys.stderr)
        print("STDOUT:", build_res.stdout, file=sys.stderr)
        print("STDERR:", build_res.stderr, file=sys.stderr)
        if is_temp_src:
            shutil.rmtree(go_src_dir, ignore_errors=True)
        shutil.rmtree(temp_bin_dir, ignore_errors=True)
        sys.exit(1)

    print("Running Go implementation against inputs via stdin...")
    with open(inputs_path, "rb") as f:
        input_bytes = f.read()

    run_res = subprocess.run(
        [str(bin_path)],
        input=input_bytes,
        capture_output=True,
        env=env,
    )

    if run_res.returncode != 0:
        print(f"Go binary exited with non-zero status: {run_res.returncode}", file=sys.stderr)
        print("STDERR:", run_res.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        if is_temp_src:
            shutil.rmtree(go_src_dir, ignore_errors=True)
        shutil.rmtree(temp_bin_dir, ignore_errors=True)
        sys.exit(1)

    actual_output = run_res.stdout.decode("utf-8", errors="replace")
    actual_lines = actual_output.splitlines()

    total = min(len(inputs), len(expected))
    matches = 0
    mismatches = []

    for i in range(total):
        orig_input = inputs[i]
        exp_output = expected[i]
        act_output = actual_lines[i] if i < len(actual_lines) else "<NO OUTPUT - TRUNCATED>"

        if act_output == exp_output:
            matches += 1
        else:
            mismatches.append({
                "line": i + 1,
                "input": orig_input,
                "expected": exp_output,
                "actual": act_output,
            })

    print("\n" + "=" * 70)
    print(f"RESULTS: {matches}/{total} matched ({matches/total*100:.2f}%)")
    print(f"Total mismatches: {len(mismatches)}")
    print("=" * 70 + "\n")

    if not mismatches:
        print("No mismatches found! The Go output matches expected Python output 100% byte-for-byte.")
    else:
        print(f"First {min(10, len(mismatches))} mismatches:\n")
        for idx, m in enumerate(mismatches[:10], start=1):
            print(f"Mismatch #{idx} (Line {m['line']}):")
            print(f"  1. Original input       : {m['input']}")
            print(f"  2. Expected Python output: {m['expected']}")
            print(f"  3. Actual Go output     : {m['actual']}")
            print("-" * 70)

    # Clean up
    if is_temp_src:
        shutil.rmtree(go_src_dir, ignore_errors=True)
    shutil.rmtree(temp_bin_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
