import os
import shutil
import subprocess
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

_TIMEOUT_SEC = 300
_DATA = Path(__file__).resolve().parent.parent / "data"
_JAIL = Path("/tmp/jail-no-python")
_FLOOR = 0.9


def run_jailed(workspace: Path, jail: Path, stdin: bytes):
    """Same jail as behaviour.py: static binary, empty chroot, user nobody."""
    shutil.rmtree(jail, ignore_errors=True)
    jail.mkdir(parents=True)
    env = dict(os.environ, CGO_ENABLED="0")
    try:
        build = subprocess.run(
            ["go", "build", "-o", str(jail / "port"), "."],
            cwd=workspace,
            env=env,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if build.returncode != 0:
        return None
    jail.chmod(0o755)
    (jail / "port").chmod(0o755)
    try:
        run = subprocess.run(
            ["chroot", "--userspec=65534:65534", str(jail), "/port"],
            input=stdin,
            timeout=_TIMEOUT_SEC,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    return run.stdout


def share_right(answers: bytes, got: bytes) -> float:
    want = answers.split(b"\n")
    if want and want[-1] == b"":
        want.pop()
    if not want:
        return 0.0
    lines = got.split(b"\n")
    right = sum(1 for i, line in enumerate(want) if i < len(lines) and lines[i] == line)
    return right / len(want)


@criterion
def no_python(workspace: Path) -> bool:
    """No .py file left, and paid only when the Go program itself earns behaviour (above 90% right)."""
    if any(workspace.rglob("*.py")):
        return False
    inputs = (_DATA / "inputs.txt").read_bytes()
    answers = (_DATA / "answers.txt").read_bytes()
    got = run_jailed(workspace, _JAIL, inputs)
    if got is None:
        return False
    return share_right(answers, got) > _FLOOR


rk.no_python()
