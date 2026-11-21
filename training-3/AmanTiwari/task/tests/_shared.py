"""Shared helpers for the checks (no criteria defined here).

Hardening note (Day 5): the hard rules (build, no_python, no_exec) are GATES, not
points. reward.toml pays only `behaviour`, and `behaviour` returns 0 unless every
gate passes. This removes the free credit a do-nothing or half port used to get.
"""

import os
import pwd
import re
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
RUN_USER = "runner"

# A pure-stdlib titlecase port never needs to start another process or step outside
# the Go memory model. Banning these makes "embed the Python source and run it with
# os/exec" impossible, whichever module the import is hidden in.
FORBIDDEN_IMPORTS = {"os/exec", "syscall", "unsafe", "plugin", "runtime/cgo"}
FORBIDDEN_TEXT = re.compile(r"\bStartProcess\b|go:linkname")

GO_ENV = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off",
              GOFLAGS="-buildvcs=false", CGO_ENABLED="0")


def _go(args, workspace: Path):
    return subprocess.run(["go", *args], cwd=workspace, env=GO_ENV,
                          capture_output=True, timeout=300)


def go_build_all(workspace: Path) -> bool:
    """`go build ./...` in the repo. True if it passes."""
    if not (workspace / "go.mod").is_file():
        return False
    try:
        return _go(["build", "./..."], workspace).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def build_binary(workspace: Path, out: Path) -> bool:
    """Build the module-root main package to `out`."""
    if not (workspace / "go.mod").is_file():
        return False
    try:
        r = _go(["build", "-o", str(out), "."], workspace)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0 and out.is_file()


def no_exec_ok(workspace: Path) -> bool:
    """The author's own code starts no process and uses no raw-memory escape hatch.

    Checks the DIRECT imports of every package the author wrote (`go list ./...`),
    not the full stdlib closure: packages like `os` and `bufio` pull in `syscall`
    and `unsafe` internally, which is legitimate, so a transitive check would reject
    every honest port. A forbidden package only reaches this set if the author
    imported it on purpose, in any package of the module (e.g. a `./run` helper).

    Nested modules are rejected outright, so imports cannot be smuggled behind a
    second go.mod + `replace`. os.StartProcess (no import needed) and go:linkname
    are caught by a source-text scan.
    """
    if not (workspace / "go.mod").is_file():
        return False
    # Exactly one module: no nested go.mod to smuggle a forbidden import through.
    for mod in workspace.rglob("go.mod"):
        if mod.parent != workspace:
            return False
    try:
        r = _go(["list", "-f", "{{join .Imports \"\\n\"}}", "./..."], workspace)
    except subprocess.TimeoutExpired:
        return False
    if r.returncode != 0:
        return False
    author_imports = set(r.stdout.decode(errors="replace").split())
    if author_imports & FORBIDDEN_IMPORTS:
        return False
    for src in workspace.rglob("*.go"):
        if FORBIDDEN_TEXT.search(src.read_text(errors="replace")):
            return False
    return True


def find_py_files(workspace: Path) -> list[str]:
    found = []
    for root, _dirs, files in os.walk(workspace, followlinks=False):
        for f in files:
            if f.lower().endswith(".py"):
                found.append(os.path.join(root, f))
    return found


def no_python_ok(workspace: Path) -> bool:
    """No .py file anywhere under the workspace."""
    return not find_py_files(workspace)


def gates_pass(workspace: Path) -> bool:
    """All hard rules: build ./... passes, no .py left, no subprocess/raw-syscall."""
    return (go_build_all(workspace)
            and no_python_ok(workspace)
            and no_exec_ok(workspace))


def run_as_runner(binary: Path, stdin: bytes, timeout: int = 120) -> bytes | None:
    """Run the agent's program as an unprivileged user (cannot read /tests)."""
    pw = pwd.getpwnam(RUN_USER)
    os.chmod(binary, 0o755)
    try:
        r = subprocess.run([str(binary)], input=stdin, capture_output=True,
                           timeout=timeout, user=pw.pw_uid, group=pw.pw_gid,
                           extra_groups=[], cwd="/tmp",
                           env={"PATH": "/usr/bin:/bin", "HOME": pw.pw_dir})
    except subprocess.TimeoutExpired:
        return None
    return r.stdout
