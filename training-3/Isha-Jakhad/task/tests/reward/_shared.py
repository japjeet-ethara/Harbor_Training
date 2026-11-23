"""Shared hard-rule gates for the task's reward checks."""

import os
import re
import subprocess
from pathlib import Path

FORBIDDEN_IMPORTS = {"os/exec", "syscall", "unsafe", "plugin", "runtime/cgo"}
FORBIDDEN_SOURCE = re.compile(
    r"\bStartProcess\b|go:linkname|^\s*import\s+(?:\(\s*)?(?:C\b|[\"']C[\"'])",
    re.M,
)
GO_ENV = dict(
    os.environ,
    GOTOOLCHAIN="local",
    GOPROXY="off",
    GOFLAGS="-buildvcs=false",
    CGO_ENABLED="0",
)


def _go(args: list[str], workspace: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["go", *args],
        cwd=workspace,
        env=GO_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )


def go_build_all(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    try:
        return _go(["build", "./..."], workspace).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def build_binary(workspace: Path, output: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    try:
        result = _go(["build", "-o", str(output), "."], workspace)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and output.is_file()


def no_python_ok(workspace: Path) -> bool:
    return not any(path.suffix.lower() == ".py" for path in workspace.rglob("*"))


def no_exec_ok(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    if any(path.name == "go.mod" and path.parent != workspace for path in workspace.rglob("go.mod")):
        return False
    try:
        result = _go(
            ["list", "-f", "{{join .Imports \"\\n\"}}", "./..."],
            workspace,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    imports = set(result.stdout.decode("utf-8", errors="replace").split())
    if imports & FORBIDDEN_IMPORTS:
        return False
    for source in workspace.rglob("*.go"):
        try:
            if FORBIDDEN_SOURCE.search(source.read_text(encoding="utf-8", errors="replace")):
                return False
        except OSError:
            return False
    return True


def gates_pass(workspace: Path) -> bool:
    return go_build_all(workspace) and no_python_ok(workspace) and no_exec_ok(workspace)


def run_as_runner(binary: Path, stdin: bytes, user, timeout: int = 120) -> bytes | None:
    os.chmod(binary, 0o755)
    try:
        result = subprocess.run(
            [str(binary)],
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            user=user.pw_uid,
            group=user.pw_gid,
            extra_groups=[],
            cwd="/tmp",
            env={"PATH": "/usr/bin:/bin", "HOME": user.pw_dir},
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout
