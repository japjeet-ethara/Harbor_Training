"""Shared grading logic for build.py, no_python.py and behaviour.py (hardened on Day 5).

This file has no criterion of its own, so rewardkit does not score it; the three
criterion files import it, so the port is built and run only once.

How the holes from the Day 4 attack are closed:

* Cheat 3 read /tests/data/hidden_expected.txt because the old grader ran the
  port as root next to /tests. Now the port runs in a chroot "jail": an empty
  directory that holds only the port's static binary, as the unprivileged
  user nobody (65534). Inside it there is no /tests, no Python, no shell and
  no other program, so the port can only read stdin and write stdout.
  This also stops "Python inside" cheats (shipping the original Python under
  another name and calling python3 from Go): there is no python3 to call.
* cgo is switched off (CGO_ENABLED=0), so C code cannot be built in, and the
  binary is static so it runs inside the empty jail.
* Cheat 1 got 1/3 for free from build + no_python. Now build and no_python
  only give points when the port is also a real port (behaviour >= GATE).
* The exam is 100,000 titles made with the kit (seed 1), answers frozen twice
  from python-titlecase in `re` mode (no `regex` package).
"""

import functools
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

REPO = Path("/workspace/repo")
INPUTS = Path("/tests/data/inputs.txt")
ANSWERS = Path("/tests/data/answers.txt")
BUILD_OUT = Path("/tmp/grade-build-all")
NOBODY = "65534"
GATE = 0.5  # build / no_python count only if at least half the titles are right
RUN_TIMEOUT = 180

# rewardkit runs build, no_python and behaviour at the same time in threads.
# One lock makes every check below run exactly once; the others wait and reuse it.
_LOCK = threading.RLock()


def _once(fn):
    cached = functools.cache(fn)

    @functools.wraps(fn)
    def wrapper():
        with _LOCK:
            return cached()

    return wrapper


def _go_env() -> dict:
    env = dict(os.environ)
    env.update(
        GOTOOLCHAIN="local",
        GOCACHE="/tmp/go-build",
        GOFLAGS="-mod=mod",
        GOPROXY="off",
        CGO_ENABLED="0",
    )
    return env


def _go(*args: str) -> bool:
    try:
        proc = subprocess.run(
            ["go", *args],
            cwd=str(REPO),
            capture_output=True,
            timeout=RUN_TIMEOUT,
            env=_go_env(),
        )
    except Exception:
        return False
    return proc.returncode == 0


@_once
def builds() -> bool:
    """`go build ./...` passes (binaries go to a scratch dir, see instruction.md tip)."""
    if not (REPO / "go.mod").is_file():
        return False
    BUILD_OUT.mkdir(parents=True, exist_ok=True)
    return _go("build", "-o", str(BUILD_OUT) + "/", "./...")


@_once
def no_python_files() -> bool:
    return not any(p.is_file() for p in REPO.rglob("*.py"))


@_once
def behaviour() -> float:
    """Share of the 100,000 hidden titles the port reproduces byte for byte."""
    if not (REPO / "go.mod").is_file():
        return 0.0

    # Fresh, empty jail that only root can change; it holds nothing but the binary.
    jail = Path(tempfile.mkdtemp(prefix="grade-jail-"))
    try:
        return _score_in_jail(jail)
    finally:
        shutil.rmtree(jail, ignore_errors=True)


def _score_in_jail(jail: Path) -> float:
    jail.chmod(0o755)  # nobody (65534) can enter and run the binary; only root can change it
    binary = jail / "titlecase"
    if not _go("build", "-o", str(binary), "."):
        return 0.0
    binary.chmod(0o755)

    want = ANSWERS.read_bytes().split(b"\n")
    if want and want[-1] == b"":
        want.pop()
    if not want:
        return 0.0

    try:
        proc = subprocess.run(
            [
                "/usr/sbin/chroot",
                f"--userspec={NOBODY}:{NOBODY}",
                f"--groups={NOBODY}",
                str(jail),
                "/titlecase",
            ],
            input=INPUTS.read_bytes(),
            capture_output=True,
            timeout=RUN_TIMEOUT,
            env={"LANG": "C.UTF-8"},
        )
    except Exception:
        return 0.0
    if proc.returncode != 0:
        return 0.0

    got = proc.stdout.split(b"\n")
    if got and got[-1] == b"":
        got.pop()
    correct = sum(1 for i, line in enumerate(want) if i < len(got) and got[i] == line)
    return correct / len(want)


def is_real_port() -> bool:
    return behaviour() >= GATE
