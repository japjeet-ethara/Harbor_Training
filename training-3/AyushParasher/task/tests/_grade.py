"""Shared grading helper. Defines no criteria, so rewardkit does not score it.

The program under test must never see the answers. So:
  1. inputs and answers are read into memory here, as root;
  2. /tests is chmod 700 by test.sh, so only root can read it;
  3. the binary is built into a fresh temp dir and run as user `nobody`
     (setpriv, no new privileges, empty env, cwd = that temp dir).
`nobody` cannot read /tests, /root (where rewardkit's Python lives) or
/proc/1/root, and the verifier image has no system Python (see Dockerfile).
"""
import functools
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
NOBODY = "65534"


def go_build_all(workspace: Path) -> bool:
    """`go build ./...` passes (output thrown away)."""
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace,
                           capture_output=True, timeout=600)
    except Exception:
        return False
    return r.returncode == 0


def no_py_files(workspace: Path) -> bool:
    return not any(p.is_file() for p in workspace.rglob("*.py"))


@functools.lru_cache(maxsize=None)
def behaviour_score(workspace: Path) -> float:
    """Share of exam titles the port cases exactly like the Python original."""
    inputs = (DATA / "inputs.txt").read_bytes()
    expected = (DATA / "answers.txt").read_bytes().split(b"\n")[:-1]
    if not expected:
        return 0.0
    tmp = tempfile.mkdtemp(prefix="tc-grade-")
    try:
        os.chmod(tmp, 0o755)
        binary = os.path.join(tmp, "titlecase-under-test")
        b = subprocess.run(["go", "build", "-o", binary, "."], cwd=workspace,
                           capture_output=True, timeout=600)
        if b.returncode != 0:
            return 0.0
        os.chmod(binary, 0o755)
        run = subprocess.run(
            ["setpriv", "--reuid", NOBODY, "--regid", NOBODY, "--clear-groups",
             "--no-new-privs", binary],
            input=inputs, capture_output=True, timeout=300, cwd=tmp,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"},
        )
    except Exception:
        return 0.0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    actual = run.stdout.split(b"\n")
    good = sum(1 for i, e in enumerate(expected) if i < len(actual) and actual[i] == e)
    return good / len(expected)
