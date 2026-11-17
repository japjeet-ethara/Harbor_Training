#!/usr/bin/env python3
"""Run solution/solve.sh in the task image and diff its output on inputs.txt.

Uses the VISIBLE set only (tests/data/inputs.txt vs expected.txt), like the
brief asks for Step 6. Prints the first N lines that differ.

Usage:  python tools/compare_visible.py [N]      (run from titlecase-project/)
Needs:  the task image built as `titlecase-go-env`
        (docker build -t titlecase-go-env titlecase-go/environment)
"""

import subprocess
import sys
import tempfile
from pathlib import Path

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
TASK = Path(__file__).resolve().parent.parent / "titlecase-go"
DATA = TASK / "tests" / "data"
IMAGE = "titlecase-go-env"


def docker(*args, **kw):
    return subprocess.run(["docker", *args], check=True, capture_output=True, **kw)


def main():
    inputs = (DATA / "inputs.txt").read_bytes()
    expected = (DATA / "expected.txt").read_bytes().split(b"\n")[:-1]

    script = (
        "bash /tmp/solve.sh >/dev/null && "
        "go build -o /tmp/tc . && /tmp/tc < /tmp/inputs.txt > /tmp/out.txt"
    )
    cid = docker("create", IMAGE, "bash", "-c", script, text=True).stdout.strip()
    try:
        docker("cp", str(TASK / "solution" / "solve.sh"), f"{cid}:/tmp/solve.sh")
        docker("cp", str(DATA / "inputs.txt"), f"{cid}:/tmp/inputs.txt")
        r = subprocess.run(["docker", "start", "-a", cid], capture_output=True, text=True)
        if r.returncode != 0:
            print("solve.sh / build / run FAILED:\n" + r.stdout + r.stderr)
            sys.exit(1)
        with tempfile.TemporaryDirectory() as tmp:
            docker("cp", f"{cid}:/tmp/out.txt", tmp)
            actual = (Path(tmp) / "out.txt").read_bytes().split(b"\n")
    finally:
        subprocess.run(["docker", "rm", "-f", cid], capture_output=True)

    input_lines = inputs.split(b"\n")
    diffs = [i for i, exp in enumerate(expected)
             if (actual[i] if i < len(actual) else None) != exp]
    print(f"{len(expected) - len(diffs)}/{len(expected)} visible lines match, "
          f"{len(diffs)} differ.")
    for i in diffs[:N]:
        got = actual[i] if i < len(actual) else None
        print(f"\nline {i + 1}")
        print(f"  input   : {input_lines[i].decode('utf-8', 'replace')!r}")
        print(f"  expected: {expected[i].decode('utf-8', 'replace')!r}")
        print(f"  actual  : {got.decode('utf-8', 'replace') if got is not None else None!r}")


if __name__ == "__main__":
    main()
