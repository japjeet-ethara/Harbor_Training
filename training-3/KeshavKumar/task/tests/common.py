"""Shared helpers for the titlecase-go checks.

This file registers no criteria, so Reward Kit ignores it as a scoring input.
Every helper catches its own errors and reports failure as a score of 0:
an exception inside a criterion would crash the whole Reward Kit run.

Hardening (Day 5):
- The exam is tests/data/inputs.txt + answers.txt: 100,000 titles, answers frozen
  from the original python-titlecase WITHOUT the `regex` package (kit/answers.py).
- The agent's program never runs as root. It runs as `nobody`, which cannot read
  /tests (chmod 700 in test.sh and tests/Dockerfile), /root (where Reward Kit's
  Python lives) or /logs/verifier. The grader reads the answers into memory first.
- After the program exits, every process left behind by `nobody` is killed, so it
  cannot change anything once grading moves on.
- The verifier has no network (task.toml), so the program cannot fetch answers.
- Behaviour credit starts above a floor: a port that gets half the titles wrong
  earns nothing for behaviour (see BEHAVIOUR_FLOOR).
"""

import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
LOG_DIR = Path("/logs/verifier")

EXAM_INPUTS = DATA_DIR / "inputs.txt"
EXAM_ANSWERS = DATA_DIR / "answers.txt"

BUILD_TIMEOUT_SEC = 300
RUN_TIMEOUT_SEC = 300

# The agent's program runs as this unprivileged user (exists in golang:1.23).
RUN_UID = 65534  # nobody
RUN_GID = 65534  # nogroup
RUN_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C.UTF-8"}

# behaviour credit = (share - FLOOR) / (1 - FLOOR), and 0 when share <= FLOOR.
# 100% right -> 1.0, 99% -> 0.98, 75% -> 0.5, 50% or less -> 0.
BEHAVIOUR_FLOOR = 0.5

# no_python only pays when the port does real work: at least this share of
# exam lines must be correct. Stops "trivial program + delete .py" cheats.
NO_PYTHON_MIN_SHARE = 0.5

REQUIRE_DIRECTIVE = re.compile(r"^\s*require\b", re.MULTILINE)

_GO = shutil.which("go") or "/usr/local/go/bin/go"
# Building runs as root, so turn off everything that could run agent code or
# reach outside the module: no cgo, no toolchain download, no module proxy.
_BUILD_ENV = {
    **os.environ,
    "GOFLAGS": "-buildvcs=false",
    "CGO_ENABLED": "0",
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
}

_lock = threading.Lock()
_build_cache: dict[str, tuple[bool, str]] = {}
_behaviour_lock = threading.Lock()
_behaviour_cache: dict[str, tuple[float, str]] = {}


def copy_repo(workspace: Path) -> Path:
    """Copy the agent's repo to a temp dir so checks never touch the original."""
    tmp = Path(tempfile.mkdtemp(prefix="titlecase-check-"))
    dst = tmp / "repo"
    shutil.copytree(workspace, dst, symlinks=True)
    return dst


def run_go(args: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [_GO, *args], cwd=cwd, env=_BUILD_ENV,
            capture_output=True, text=True, timeout=BUILD_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return False, f"go {' '.join(args)} timed out after {BUILD_TIMEOUT_SEC}s"
    except OSError as e:
        return False, f"could not run go: {e}"
    if r.returncode != 0:
        return False, f"go {' '.join(args)} failed:\n{(r.stdout + r.stderr)[-2000:]}"
    return True, f"go {' '.join(args)} passed"


def build_status(workspace: Path) -> tuple[bool, str]:
    """Build check: go.mod exists, has no `require`, and `go build ./...` passes.

    Cached, so the three checks build the repo only once.
    """
    key = str(workspace)
    with _lock:
        if key not in _build_cache:
            _build_cache[key] = _build_status(Path(workspace))
        return _build_cache[key]


def _build_status(workspace: Path) -> tuple[bool, str]:
    try:
        gomod = workspace / "go.mod"
        if not gomod.is_file():
            return False, "no go.mod in /workspace/repo"
        if REQUIRE_DIRECTIVE.search(gomod.read_text(encoding="utf-8", errors="replace")):
            return False, "go.mod has a require directive (standard library only)"
        repo = copy_repo(workspace)
        try:
            # `-o /dev/null` = compile everything but discard the output. Plain
            # `go build ./...` with one main package tries to write a binary named
            # after the module, which fails if a folder of that name exists.
            return run_go(["build", "-o", "/dev/null", "./..."], repo)
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)
    except Exception as e:  # never crash the Reward Kit run
        return False, f"build check error: {e!r}"


def find_py_files(workspace: Path) -> list[str]:
    found = []
    for root, dirs, files in os.walk(workspace):
        for name in files + dirs:
            if name.endswith(".py"):
                found.append(os.path.relpath(os.path.join(root, name), workspace))
    return sorted(found)


def _kill_leftovers() -> None:
    """Kill every process still running as `nobody` (daemons, children, ...).

    `kill -KILL -1` sent BY nobody reaches every process nobody owns, itself included.
    Run twice in case a process forked while the first round was running.
    """
    for _ in range(2):
        try:
            subprocess.run(
                ["/bin/sh", "-c", "kill -KILL -1"], user=RUN_UID, group=RUN_GID,
                extra_groups=[], env=RUN_ENV, cwd="/", capture_output=True, timeout=30,
            )
        except Exception:
            pass


def behaviour_share(workspace: Path) -> tuple[float, str]:
    """Share of exam lines whose output line matches byte for byte (0.0 to 1.0).

    Cached, so behaviour and no_python run the program only once.
    """
    key = str(workspace)
    with _behaviour_lock:
        if key not in _behaviour_cache:
            _behaviour_cache[key] = _behaviour_share(Path(workspace))
        return _behaviour_cache[key]


def behaviour_credit(share: float) -> float:
    if share <= BEHAVIOUR_FLOOR:
        return 0.0
    return (share - BEHAVIOUR_FLOOR) / (1.0 - BEHAVIOUR_FLOOR)


def _behaviour_share(workspace: Path) -> tuple[float, str]:
    try:
        # Read the key into the grader's memory BEFORE the agent's program starts.
        inputs = EXAM_INPUTS.read_bytes()
        expected = EXAM_ANSWERS.read_bytes().split(b"\n")
        if expected and expected[-1] == b"":
            expected.pop()                      # file ends with "\n"
        input_lines = inputs.split(b"\n")

        if not (workspace / "go.mod").is_file():
            return 0.0, "no go.mod in /workspace/repo"
        repo = copy_repo(workspace)
        try:
            binary = repo.parent / "titlecase-go-bin"
            ok, why = run_go(["build", "-o", str(binary), "."], repo)
            if not ok:
                return 0.0, why
            # nobody needs to reach and execute the binary, nothing more.
            os.chmod(repo.parent, 0o711)
            os.chmod(binary, 0o711)
            try:
                r = subprocess.run(
                    [str(binary)], input=inputs, capture_output=True,
                    timeout=RUN_TIMEOUT_SEC, cwd="/", env=RUN_ENV,
                    user=RUN_UID, group=RUN_GID, extra_groups=[],
                )
                stdout, note = r.stdout, f"exit code {r.returncode}"
            except subprocess.TimeoutExpired as e:
                stdout, note = e.stdout or b"", f"timed out after {RUN_TIMEOUT_SEC}s"
            finally:
                _kill_leftovers()
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

        actual = stdout.split(b"\n")
        mismatches = []
        matched = 0
        for i, exp in enumerate(expected):
            got = actual[i] if i < len(actual) else None
            if got == exp:
                matched += 1
            elif len(mismatches) < 50:
                mismatches.append((i + 1, input_lines[i], exp, got))
        _write_mismatches(mismatches, matched, len(expected))
        share = matched / len(expected)
        return share, f"{matched}/{len(expected)} exam lines match exactly ({note})"
    except Exception as e:  # never crash the Reward Kit run
        return 0.0, f"behaviour check error: {e!r}"


def _write_mismatches(mismatches, matched: int, total: int) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_DIR / "behaviour_mismatches.txt", "w", encoding="utf-8") as f:
            f.write(f"{matched}/{total} lines match. First {len(mismatches)} mismatches:\n\n")
            for line_no, inp, exp, got in mismatches:
                f.write(f"line {line_no}\n  input   : {inp!r}\n  expected: {exp!r}\n  actual  : {got!r}\n\n")
    except OSError:
        pass
