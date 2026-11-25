"""Shared build, security, and gating helpers. Registers no Reward Kit criteria."""

import fcntl
import os
import subprocess
from pathlib import Path

HIDDEN_INPUTS = Path(__file__).resolve().parent / "data" / "inputs.txt"
HIDDEN_ANSWERS = Path(__file__).resolve().parent / "data" / "answers.txt"

BANNED_IMPORTS = {"os/exec", "syscall", "plugin", "runtime/cgo"}
BANNED_CALLS = (b"StartProcess", b"exec.Command", b"syscall.Exec", b"syscall.ForkExec")
PYTHON_SIGNATURES = (b"def titlecase(", b"SMALL = ", b"import regex", b"#!/usr/bin/env python", b"#!/usr/bin/python")


def _drop_privileges() -> None:
    os.setgid(65534)
    os.setuid(65534)


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\r\n"):
        data = data[:-2]
    elif data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return [line.rstrip(b"\r") for line in data.split(b"\n")]


def go_build(workspace: Path, args: list[str], timeout: int = 180) -> bool:
    """Run `go <args>` in the workspace. Concurrent builds take one lock."""
    if not workspace.is_dir():
        return False
    lock_path = Path("/tmp/titlecase-go-build.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            result = subprocess.run(
                ["go", *args],
                cwd=workspace,
                capture_output=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False

    return result.returncode == 0


def workspace_is_clean_go(workspace: Path) -> bool:
    """Ensure no Python files/artifacts, only Go stdlib, and no process-spawning tricks."""
    if not workspace.is_dir():
        return False

    for path in workspace.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir() and path.name == "__pycache__":
            return False
        if path.is_file():
            if path.suffix.lower() in {".py", ".pyc", ".pyo", ".pyd"}:
                return False
            try:
                raw = path.read_bytes()
            except OSError:
                return False
            if path.suffix == ".go":
                if any(call in raw for call in BANNED_CALLS):
                    return False
            else:
                if any(sig in raw for sig in PYTHON_SIGNATURES):
                    return False

    go_mod = workspace / "go.mod"
    if go_mod.is_file():
        mod_text = go_mod.read_text(encoding="utf-8", errors="ignore")
        if "require " in mod_text or "require(" in mod_text:
            return False

    try:
        direct = subprocess.run(
            ["go", "list", "-f", "{{range .Imports}}{{.}}{{println}}{{end}}", "./..."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if direct.returncode != 0:
            return False
        for imp in direct.stdout.splitlines():
            imp = imp.strip()
            if imp in BANNED_IMPORTS:
                return False

        deps = subprocess.run(
            ["go", "list", "-deps", "-f", "{{.Standard}}|{{.ImportPath}}", "./..."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if deps.returncode != 0:
            return False
        own_mod = subprocess.run(
            ["go", "list", "-m"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
        for line in deps.stdout.splitlines():
            if "|" not in line:
                continue
            is_std, imp = line.split("|", 1)
            if is_std != "true" and imp != own_mod and not imp.startswith(own_mod + "/"):
                return False
    except (OSError, subprocess.TimeoutExpired):
        return False

    return True


def evaluate_behaviour_raw(workspace: Path) -> float:
    """Build and run the candidate binary as unprivileged `nobody` in /tmp."""
    if not workspace_is_clean_go(workspace):
        return 0.0
    if not HIDDEN_INPUTS.is_file() or not HIDDEN_ANSWERS.is_file():
        return 0.0

    expected = _lines(HIDDEN_ANSWERS.read_bytes())
    if not expected:
        return 0.0

    binary = Path("/tmp/titlecase-behaviour")
    if not go_build(workspace, ["build", "-o", str(binary), "."]):
        return 0.0

    try:
        binary.chmod(0o755)
        result = subprocess.run(
            [str(binary)],
            input=HIDDEN_INPUTS.read_bytes(),
            capture_output=True,
            cwd="/tmp",
            preexec_fn=_drop_privileges,
            env={"PATH": "", "HOME": "/nonexistent"},
            timeout=120,
        )
        if result.returncode != 0:
            return 0.0
    except (OSError, subprocess.TimeoutExpired):
        return 0.0

    actual = _lines(result.stdout)
    matches = sum(
        1 for idx, line in enumerate(expected) if idx < len(actual) and actual[idx] == line
    )
    return matches / len(expected)