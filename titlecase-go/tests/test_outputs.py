"""Shared Reward Kit checks for the titlecase Go port.

Each check is registered from its own directory so Reward Kit emits one score
per check. The directories call these shared criteria; this module does not
register a score itself.
"""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
BINARY = Path("/opt/titlecase-verify")
RUN_USER = "titlecase"
_GO_LOCK = threading.Lock()


def _go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOTOOLCHAIN"] = "local"
    env["GOFLAGS"] = "-mod=readonly"
    return env


def _run_go(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess[bytes] | None:
    try:
        with _GO_LOCK:
            return subprocess.run(
                args,
                cwd=str(REPO),
                env=_go_env(),
                capture_output=True,
                timeout=timeout,
            )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _go_ok(args: list[str]) -> bool:
    if not REPO.is_dir():
        return False
    result = _run_go(args)
    return result is not None and result.returncode == 0


def _has_python_files(root: Path) -> bool:
    if not root.is_dir():
        return False
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        for name in filenames:
            if name.endswith(".py"):
                return True
    return False


def _build_binary(dest: Path) -> bool:
    if not REPO.is_dir():
        return False
    if dest.exists():
        dest.unlink()
    built = _run_go(["go", "build", "-o", str(dest), "."])
    if built is not None and built.returncode == 0 and dest.is_file():
        dest.chmod(0o755)
        return True
    if dest.exists():
        dest.unlink()

    listed = _run_go(["go", "list", "-f", "{{.Name}}\t{{.Dir}}", "./..."])
    if listed is None or listed.returncode != 0:
        return False
    mains: list[str] = []
    for line in listed.stdout.decode("utf-8", errors="replace").splitlines():
        name, separator, directory = line.partition("\t")
        if separator and name == "main" and directory:
            mains.append(directory)
    if str(REPO) in mains:
        target = str(REPO)
    elif len(mains) == 1:
        target = mains[0]
    else:
        return False
    built = _run_go(["go", "build", "-o", str(dest), target])
    if built is None or built.returncode != 0 or not dest.is_file():
        return False
    dest.chmod(0o755)
    return True


def _line_score(expected: bytes, actual: bytes) -> float:
    try:
        expected_lines = expected.decode("utf-8").splitlines()
        actual_lines = actual.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return 0.0
    total = max(len(expected_lines), len(actual_lines))
    if total == 0:
        return 1.0
    matches = sum(
        1
        for index, line in enumerate(expected_lines)
        if index < len(actual_lines) and actual_lines[index] == line
    )
    return matches / total


@criterion(shared=True, description="go build ./... succeeds in /workspace/repo")
def build(workspace: Path) -> bool:
    del workspace
    return _go_ok(["go", "build", "./..."])


@criterion(
    shared=True,
    description="no .py files remain under /workspace/repo and go build ./... succeeds",
)
def no_python(workspace: Path) -> bool:
    del workspace
    if not REPO.is_dir() or _has_python_files(REPO):
        return False
    return _go_ok(["go", "build", "./..."])


@criterion(
    shared=True,
    description="fraction of hidden title lines that match exactly",
)
def behaviour(workspace: Path) -> float:
    del workspace
    try:
        if not _build_binary(BINARY):
            return 0.0
        completed = subprocess.run(
            [str(BINARY)],
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            cwd="/tmp",
            user=RUN_USER,
            timeout=120,
        )
        if completed.returncode != 0:
            return 0.0
    except (OSError, subprocess.SubprocessError):
        return 0.0
    return _line_score(HIDDEN_EXPECTED.read_bytes(), completed.stdout)
