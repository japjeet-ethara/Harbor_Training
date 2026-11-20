"""Shared grading helpers for the Reward Kit checks in /tests/checks.

Each check file imports this module; Python caches it, so the build and the
hidden-set run happen once even though Reward Kit runs the checks in parallel.
"""

from __future__ import annotations

import functools
import os
import subprocess
import tempfile
import threading
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
HIDDEN_INPUTS = TESTS / "data" / "hidden_inputs.txt"
HIDDEN_EXPECTED = TESTS / "data" / "hidden_expected.txt"
BUILD_TIMEOUT = 300
RUN_TIMEOUT = 60
MAX_STDOUT = 32 << 20

_lock = threading.Lock()
_WORK = Path(tempfile.mkdtemp(prefix="titlecase-grade-"))


def log(msg: str) -> None:
    print(msg, flush=True)


def go_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(GOTOOLCHAIN="local", GOPROXY="off", GOFLAGS="", GOENV="off")
    env.setdefault("GOCACHE", str(_WORK / "gocache"))
    return env


def _go(workspace: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(["go", *args], cwd=workspace, env=go_env(), text=True,
                              capture_output=True, timeout=BUILD_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"go {' '.join(args)}: {exc}")
        return None


@functools.cache
def build_ok(workspace: Path) -> bool:
    """`go build ./...` passes and every dependency is in the standard library."""
    with _lock:
        if not (workspace / "go.mod").is_file():
            log("[build] no go.mod in the repository")
            return False
        r = _go(workspace, "build", "./...")
        if r is None or r.returncode != 0:
            log("[build] go build ./... failed:\n" + (r.stderr[-3000:] if r else ""))
            return False
        fmt = ("{{if not .Standard}}{{if not .Module}}{{.ImportPath}}\n"
               "{{else if not .Module.Main}}{{.ImportPath}}\n{{end}}{{end}}")
        r = _go(workspace, "list", "-deps", "-f", fmt, "./...")
        if r is None or r.returncode != 0:
            log("[build] go list failed:\n" + (r.stderr[-3000:] if r else ""))
            return False
        outside = [p for p in r.stdout.split() if p]
        if outside or (workspace / "vendor").exists():
            log(f"[build] non-standard dependencies: {outside[:5]} vendor={((workspace / 'vendor').exists())}")
            return False
        log("[build] ok")
        return True


def py_files(workspace: Path) -> list[Path]:
    found = []
    for root, _dirs, files in os.walk(workspace):
        found += [Path(root) / f for f in files if f.lower().endswith(".py")]
    return found


@functools.cache
def hidden_results(workspace: Path) -> tuple[int, int, int]:
    """Return (matched, total, matched lines that the program had to change)."""
    with _lock:
        inputs = HIDDEN_INPUTS.read_bytes().split(b"\n")[:-1]
        expected = HIDDEN_EXPECTED.read_bytes().split(b"\n")[:-1]
        total = len(expected)
        binary = _WORK / "titlecase"
        r = _go(workspace, "build", "-o", str(binary), ".")
        if r is None or r.returncode != 0:
            log("[behaviour] go build -o ... . failed:\n" + (r.stderr[-3000:] if r else ""))
            return 0, total, 0
        run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=_WORK))
        try:
            p = subprocess.run([str(binary)], input=HIDDEN_INPUTS.read_bytes(), cwd=run_dir,
                               capture_output=True, timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired:
            log(f"[behaviour] program did not finish within {RUN_TIMEOUT} s")
            return 0, total, 0
        except OSError as exc:
            log(f"[behaviour] cannot run the program: {exc}")
            return 0, total, 0
        got = p.stdout[:MAX_STDOUT].split(b"\n")
        matched = changed = shown = 0
        for i, want in enumerate(expected):
            if i < len(got) and got[i] == want:
                matched += 1
                changed += want != inputs[i]
            elif shown < 5:
                log(f"[behaviour] mismatch on hidden line {i + 1}")
                shown += 1
        log(f"[behaviour] {matched}/{total} hidden lines match")
        return matched, total, changed
