#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def check_no_python():
    repo = Path("/workspace/repo")
    if not repo.exists():
        repo = Path(__file__).resolve().parent.parent.parent.parent

    # Check for any .py files in repo
    py_files = list(repo.rglob("*.py"))
    if py_files:
        print(f"Found .py files in repo: {[str(p) for p in py_files[:10]]}", file=sys.stderr)
        return 0.0

    # Also verify that go build passes
    try:
        proc = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120
        )
        if proc.returncode != 0:
            print(f"Build failed in no_python check:\nSTDERR: {proc.stderr}", file=sys.stderr)
            return 0.0
    except Exception as e:
        print(f"Build check exception in no_python: {e}", file=sys.stderr)
        return 0.0

    return 1.0

if __name__ == "__main__":
    score = check_no_python()
    print(score)
    sys.exit(0 if score == 1.0 else 1)
