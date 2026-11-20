"""No-Python criterion: no sources, no interpreter, no execution escape hatch.

The old check only looked for file names ending in ".py".  It is replaced by a
source/asset/import scan, a runtime assertion that the unprivileged runner
cannot start an interpreter, and the same correctness gate as the build check.
"""

import os
import pwd
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

DATA = Path("/tests/data")
BIN = Path("/tmp/tc_nopython_bin")
MIN_ACCURACY = 0.98

PYTHON_SUFFIXES = {".py", ".pyc", ".pyo", ".pyd", ".pyw"}
FORBIDDEN_IMPORTS = re.compile(r'"(os/exec|syscall|plugin|unsafe)"')
CGO_IMPORT = re.compile(r'(?m)^\s*(?:import\s*)?\(?\s*"C"\s*\)?\s*$')
REQUIRE_LINE = re.compile(r"(?m)^\s*require\b")
# Markers that only appear in Python source or in a Python interpreter binary.
PYTHON_SOURCE_MARKERS = (
    b"def titlecase(",
    b"import regex",
    b"exec(compile(",
    b"/usr/bin/python",
    b"/usr/local/bin/python",
)
PYTHON_BINARY_MARKERS = (b"Py_Initialize", b"libpython", b"/usr/lib/python")
FORBIDDEN_CALLS = ("os.StartProcess", "exec.Command", "syscall.Exec")


def _files(workspace: Path):
    for dirpath, dirnames, filenames in os.walk(workspace, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(os.path.join(dirpath, name))]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or not path.is_file():
                continue
            yield path


def _no_python_sources(workspace: Path) -> bool:
    for path in _files(workspace):
        if path.suffix.lower() in PYTHON_SUFFIXES:
            return False
        try:
            data = path.read_bytes()
        except OSError:
            return False
        if any(marker in data for marker in PYTHON_SOURCE_MARKERS):
            return False
        if data.startswith(b"\x7fELF") and any(marker in data for marker in PYTHON_BINARY_MARKERS):
            return False
    return True


def _no_execution_escape_hatch(workspace: Path) -> bool:
    for path in _files(workspace):
        if path.suffix != ".go":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "go:embed" in text:
            return False
        if FORBIDDEN_IMPORTS.search(text) or CGO_IMPORT.search(text):
            return False
        if any(call in text for call in FORBIDDEN_CALLS):
            return False
    go_mod = workspace / "go.mod"
    if not go_mod.is_file():
        return False
    return REQUIRE_LINE.search(go_mod.read_text(encoding="utf-8", errors="replace")) is None


def _runner_cannot_start_python() -> bool:
    pw = pwd.getpwnam("runner")
    env = {"PATH": "/usr/local/go/bin:/usr/bin:/bin", "HOME": pw.pw_dir}
    for candidate in ("/usr/bin/python3", "/usr/local/bin/python3", "/usr/bin/python"):
        try:
            probe = subprocess.run(
                [candidate, "-c", "print(1)"],
                capture_output=True,
                user=pw.pw_uid,
                group=pw.pw_gid,
                env=env,
                timeout=10,
            )
        except Exception:
            continue  # missing or not executable by runner: good
        if probe.returncode == 0:
            return False
    return True


def _accuracy(stdout: bytes, expected: bytes) -> float:
    exp = expected.split(b"\n")
    if exp and exp[-1] == b"":
        exp.pop()
    got = stdout.split(b"\n")
    if got and got[-1] == b"":
        got.pop()
    if not exp:
        return 0.0
    hits = sum(1 for index, line in enumerate(exp) if index < len(got) and got[index] == line)
    return hits / len(exp)


def _exam_accuracy(workspace: Path):
    if not _runner_cannot_start_python():
        return None
    build = subprocess.run(
        ["/usr/local/go/bin/go", "build", "-o", str(BIN), "."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if build.returncode != 0 or not BIN.is_file():
        return None
    os.chmod(BIN, 0o755)
    blob = b""
    try:
        inputs = (DATA / "inputs.txt").read_bytes()
        expected = (DATA / "answers.txt").read_bytes()
        pw = pwd.getpwnam("runner")
        run = subprocess.run(
            [str(BIN)],
            cwd="/tmp",
            user=pw.pw_uid,
            group=pw.pw_gid,
            input=inputs,
            capture_output=True,
            timeout=300,
            env={"PATH": "/usr/local/go/bin:/usr/bin:/bin", "HOME": pw.pw_dir, "CGO_ENABLED": "0"},
        )
        blob = BIN.read_bytes()
    except Exception:
        return None
    finally:
        BIN.unlink(missing_ok=True)
    if run.returncode != 0:
        return None
    # A submitted binary that ships an interpreter is still a Python runtime.
    if any(marker in blob for marker in PYTHON_BINARY_MARKERS):
        return None
    return _accuracy(run.stdout, expected)


@criterion(description="no Python sources or interpreter, no exec/embed escape hatch, and matching behaviour")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    if not _no_python_sources(workspace):
        return False
    if not _no_execution_escape_hatch(workspace):
        return False
    result = subprocess.run(
        ["/usr/local/go/bin/go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        return False
    accuracy = _exam_accuracy(workspace)
    return accuracy is not None and accuracy >= MIN_ACCURACY
