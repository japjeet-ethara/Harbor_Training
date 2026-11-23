#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def check_build():
    repo = Path("/workspace/repo")
    if not repo.exists():
        repo = Path(__file__).resolve().parent.parent.parent.parent
    try:
        proc = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120
        )
        if proc.returncode == 0:
            return 1.0
        print(f"Build failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}", file=sys.stderr)
        return 0.0
    except Exception as e:
        print(f"Build check exception: {e}", file=sys.stderr)
        return 0.0

if __name__ == "__main__":
    score = check_build()
    print(score)
    sys.exit(0 if score == 1.0 else 1)
