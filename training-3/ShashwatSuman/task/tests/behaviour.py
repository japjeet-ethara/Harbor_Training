"""Check 3 (weight 4): share of 100,000 exam titles the Go program gets exactly right.

Answers are pre-loaded in memory and hashed before the candidate binary runs.
The binary is executed without access to /tests files.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

DATA = Path(__file__).resolve().parent / "data"


def _read_lines(path: Path) -> list[str]:
    text = path.read_bytes().decode("utf-8")
    return text.split("\n")[:-1]


@criterion(description="Go program output matches the original Python on the 100k exam titles")
def hidden_titles_match(workspace: Path) -> float:
    # 1. Pre-load expected outputs and compute hashes
    expected = _read_lines(DATA / "answers.txt")
    input_bytes = (DATA / "inputs.txt").read_bytes()
    expected_hashes = [hashlib.sha256(line.encode("utf-8")).digest() for line in expected]

    with tempfile.TemporaryDirectory() as tmp:
        isolated_dir = Path(tmp) / "run_sandbox"
        isolated_dir.mkdir(parents=True, exist_ok=True)
        binary = isolated_dir / "titlecase_eval"

        try:
            build = subprocess.run(
                ["go", "build", "-o", str(binary), "."],
                cwd=workspace, capture_output=True, timeout=300,
            )
            if build.returncode != 0:
                return 0.0

            # Execute binary in isolated directory
            run = subprocess.run(
                [str(binary)],
                input=input_bytes,
                cwd=str(isolated_dir),
                capture_output=True,
                timeout=180,
            )
        except Exception:
            return 0.0

    if run.returncode != 0:
        return 0.0

    got_lines = run.stdout.decode("utf-8", errors="replace").split("\n")
    if len(got_lines) > 0 and got_lines[-1] == "":
        got_lines = got_lines[:-1]

    if len(got_lines) < len(expected):
        return 0.0

    # Compare hashes line-by-line
    correct = 0
    total = len(expected)
    for i in range(total):
        got_hash = hashlib.sha256(got_lines[i].encode("utf-8")).digest()
        if got_hash == expected_hashes[i]:
            correct += 1

    return correct / total
