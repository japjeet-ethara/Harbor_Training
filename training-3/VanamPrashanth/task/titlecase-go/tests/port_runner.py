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

Hardening round 2 (self-attack, cheat N1 "download the exam"):
- The task lives in a public GitHub repo, so the stored hidden answers can be
  downloaded or copied into solve.sh. Every grading run therefore also makes a
  FRESH exam: FRESH_COUNT new titles from tests/gen.py with a random seed,
  answered by the original Python titlecase() (tests/data/original_titlecase.txt,
  WITHOUT the regex package). Nobody can know these answers in advance.
- The score uses the LOWER of the stored-exam and fresh-exam accuracies.
"""

import importlib.machinery
import importlib.util
import os
import random
import re
import secrets
import sys
import threading
import shutil
import subprocess
import tempfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
NOBODY = "65534:65534"
PASS_MARK = 0.80
FRESH_COUNT = 2000
TESTS_DIR = Path(__file__).resolve().parent
LOG_DIR = Path("/logs/verifier")
_IMPORT_LOCK = threading.Lock()
# characters str.splitlines() treats as line ends; such titles cannot be one line
LINE_BREAKS = "\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"
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


def _load_module(name: str, path: Path, loader=None):
    loader = loader or importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _original_titlecase():
    """The original Python titlecase(), loaded with the optional regex package blocked."""
    with _IMPORT_LOCK:
        saved = sys.modules.get("regex", None)
        had = "regex" in sys.modules
        sys.modules["regex"] = None  # import regex -> ImportError -> falls back to re
        try:
            mod = _load_module("titlecase_original", DATA_DIR / "original_titlecase.txt")
        finally:
            if had:
                sys.modules["regex"] = saved
            else:
                sys.modules.pop("regex", None)
    return mod.titlecase


def stored_exam():
    inputs = (DATA_DIR / "hidden_inputs.txt").read_text(encoding="utf-8").splitlines()
    expected = (DATA_DIR / "hidden_expected.txt").read_text(encoding="utf-8").splitlines()
    return inputs, expected


def fresh_exam(seed: int, count: int = FRESH_COUNT):
    """New titles nobody has seen: tests/gen.py families, random seed, answers from the original."""
    gen = _load_module(f"titlecase_gen_{seed}", TESTS_DIR / "gen.py")
    gen.random = random.Random(seed)  # private RNG, safe with concurrent criteria
    titlecase = _original_titlecase()
    known = set((DATA_DIR / "inputs.txt").read_text(encoding="utf-8").splitlines())
    known |= set((DATA_DIR / "hidden_inputs.txt").read_text(encoding="utf-8").splitlines())
    inputs, expected = [], []
    while len(inputs) < count:
        title = gen.make_title()
        if title in known or any(c in title for c in LINE_BREAKS):
            continue
        answer = titlecase(title)
        if any(c in answer for c in LINE_BREAKS):
            continue
        inputs.append(title)
        expected.append(answer)
    return inputs, expected


def run_jailed(repo: Path, input_bytes: bytes):
    """Build the port and run it alone in an empty chroot jail as nobody. Returns stdout lines or None."""
    chroot = shutil.which("chroot")
    if chroot is None or not repo.exists():
        return None
    tmp = Path(tempfile.mkdtemp(prefix="titlecase-jail-"))
    try:
        jail = tmp / "jail"
        jail.mkdir()
        os.chmod(tmp, 0o755)
        os.chmod(jail, 0o755)
        binary = jail / "port"
        if not build_binary(repo, binary):
            return None
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
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return proc.stdout.decode("utf-8", errors="replace").splitlines()


def _share(got, expected, offset: int) -> float:
    if not expected:
        return 0.0
    ok = sum(1 for i, exp in enumerate(expected) if offset + i < len(got) and got[offset + i] == exp)
    return ok / len(expected)


def hidden_accuracy(repo: Path, label: str = "check") -> float:
    """min(stored-exam accuracy, fresh-exam accuracy) of the jailed binary; 0.0 on any failure."""
    try:
        s_in, s_exp = stored_exam()
        seed = int(os.environ.get("TITLECASE_FRESH_SEED") or secrets.randbits(63))
        f_in, f_exp = fresh_exam(seed)
    except Exception as exc:  # never pay out if the exam cannot be built
        print(f"[{label}] exam build failed: {exc!r}", file=sys.stderr)
        return 0.0
    # Exam is now only in the grader's memory; the binary sees one stdin stream.
    payload = "".join(line + "\n" for line in s_in + f_in).encode("utf-8")
    got = run_jailed(repo, payload)
    if got is None:
        stored = fresh = 0.0
    else:
        stored = _share(got, s_exp, 0)
        fresh = _share(got, f_exp, len(s_in))
    result = min(stored, fresh)
    note = f"[{label}] fresh seed={seed} stored={stored:.4f} fresh={fresh:.4f} used={result:.4f}"
    print(note, file=sys.stderr)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / f"fresh-exam-{label}.txt").write_text(note + "\n", encoding="utf-8")
    except OSError:
        pass
    return result


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
