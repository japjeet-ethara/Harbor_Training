"""Shared grader helpers for build / no_python / behaviour.

This file registers no criterion, so RewardKit scores nothing from it. The three
check files load it by path.

Hardening (Day 5, closes MohammadAdnan's cheats 1-3):
- The answers are read into the grader's memory before the agent's binary runs.
- The binary runs alone in an empty chroot jail as user nobody (65534), with an
  empty environment. Inside the jail there is no /tests, no answer file, no
  python3, no shell and no other program, so it can neither read the exam
  (cheat 1) nor hand the work to Python (cheat 2).
- Accuracy below PASS_MARK earns 0 behaviour and 0 no_python, so a half port
  or a lookup table gets no partial credit (cheat 3).
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
NOBODY = "65534:65534"
PASS_MARK = 0.80
BUILD_ENV = dict(os.environ, CGO_ENABLED="0")  # static binary, runs in an empty jail

PY_SOURCE_MARKERS = (
    b"def titlecase(",
    b"#!/usr/bin/env python",
    b"#!/usr/bin/python",
)
OS_EXEC_IMPORT = re.compile(rb'"os/exec"')


def repo_dir(workspace) -> Path:
    repo = Path("/workspace/repo")
    if not repo.exists() and workspace and Path(workspace).exists():
        repo = Path(workspace)
    return repo


def go_build_all(repo: Path) -> bool:
    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo),
            capture_output=True,
            env=BUILD_ENV,
            timeout=120,
        )
        return res.returncode == 0
    except Exception:
        return False


def build_binary(repo: Path, out: Path) -> bool:
    """Build package main at the repo root, or the first package main below it."""
    try:
        res = subprocess.run(
            ["go", "build", "-o", str(out), "."],
            cwd=str(repo), capture_output=True, env=BUILD_ENV, timeout=120,
        )
        if res.returncode == 0 and out.is_file():
            return True
        res = subprocess.run(
            ["go", "list", "-f", '{{if eq .Name "main"}}{{.Dir}}{{end}}', "./..."],
            cwd=str(repo), capture_output=True, text=True, env=BUILD_ENV, timeout=60,
        )
        main_dirs = [d.strip() for d in res.stdout.splitlines() if d.strip()]
        if not main_dirs:
            return False
        res = subprocess.run(
            ["go", "build", "-o", str(out), "."],
            cwd=main_dirs[0], capture_output=True, env=BUILD_ENV, timeout=120,
        )
        return res.returncode == 0 and out.is_file()
    except Exception:
        return False


def hidden_accuracy(repo: Path) -> float:
    """Share of hidden lines the jailed binary gets exactly right (0.0 on any failure)."""
    inputs_path = DATA_DIR / "hidden_inputs.txt"
    expected_path = DATA_DIR / "hidden_expected.txt"
    if not inputs_path.is_file() or not expected_path.is_file():
        return 0.0

    # Read the exam into memory first; the binary never sees these files.
    input_bytes = inputs_path.read_bytes()
    expected = expected_path.read_text(encoding="utf-8").splitlines()
    if not expected:
        return 0.0

    chroot = shutil.which("chroot")
    if chroot is None or not repo.exists():
        return 0.0

    tmp = Path(tempfile.mkdtemp(prefix="titlecase-jail-"))
    try:
        jail = tmp / "jail"
        jail.mkdir()
        os.chmod(tmp, 0o755)
        os.chmod(jail, 0o755)
        binary = jail / "port"
        if not build_binary(repo, binary):
            return 0.0
        os.chmod(binary, 0o755)
        proc = subprocess.run(
            [chroot, f"--userspec={NOBODY}", str(jail), "/port"],
            input=input_bytes,
            capture_output=True,
            env={},
            cwd="/",
            timeout=180,
        )
    except Exception:
        return 0.0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    got = proc.stdout.decode("utf-8", errors="replace").splitlines()
    matches = sum(1 for i, exp in enumerate(expected) if i < len(got) and got[i] == exp)
    return matches / len(expected)


def graded(accuracy: float) -> float:
    """0 below PASS_MARK, then linear up to 1.0 at 100% correct."""
    if accuracy < PASS_MARK:
        return 0.0
    return (accuracy - PASS_MARK) / (1.0 - PASS_MARK)


def python_left_in_repo(repo: Path) -> bool:
    """True if Python survives in any form: a .py file, Python source under another
    name, or Go code that starts other programs (os/exec)."""
    if any(repo.rglob("*.py")):
        return True
    for path in repo.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if any(marker in data for marker in PY_SOURCE_MARKERS):
            return True
        if path.suffix == ".go" and OS_EXEC_IMPORT.search(data):
            return True
    return False
