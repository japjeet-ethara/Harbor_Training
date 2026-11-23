"""All-or-nothing behaviour check.

Exams (all must match exactly, line for line):
  * data/inputs.txt -> data/answers.txt: 100,000 random titles from the kit
    (make_pool.py 100000 1), answers frozen from python-titlecase 2.4.1
    WITHOUT the regex package (Python `re` mode).
  * data/regression_inputs.txt -> data/regression_expected.txt: the original
    2,000-line set (python-titlecase's own test cases and more), same mode.

The binary does not run under rewardkit's Worker: Worker starts a Python
bootstrap as the worker UID, so that UID must be able to run Python, and then
so could the submission (Sakshi Singh's cheat 2). Instead it runs here as
`nobody`, with no supplementary groups and no_new_privs set. tests/Dockerfile
makes every interpreter in this image unusable for non-root users, and
/tests, /logs/verifier and the workspace are made 0700 before the run.
"""

import ctypes
import os
import pwd
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {
    **os.environ,
    "CGO_ENABLED": "0",
    "GOFLAGS": "-mod=mod",
    "GOPROXY": "off",
    "GOTOOLCHAIN": "local",
    "GOWORK": "off",
}
DATA = Path("/tests/data")
EXAMS = (
    ("inputs.txt", "answers.txt"),
    ("regression_inputs.txt", "regression_expected.txt"),
)
RUN_TIMEOUT_SEC = 120
MAX_OUTPUT_BYTES = 64 * 2**20
PR_SET_NO_NEW_PRIVS = 38


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n")


def _lock_down(workspace: Path, nobody: pwd.struct_passwd) -> None:
    for path in (Path("/tests"), Path("/logs/verifier"), workspace):
        if path.is_dir():
            if path.stat().st_uid == nobody.pw_uid:
                raise RuntimeError(f"{path} is owned by the run user")
            path.chmod(0o700)
    # Root keeps its privileges; this only stops setuid binaries from adding any.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS failed")


def _run(executable: Path, stdin_data: bytes, nobody: pwd.struct_passwd):
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout:
        stdin.write(stdin_data)
        stdin.seek(0)
        process = subprocess.Popen(
            [str(executable)],
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.DEVNULL,
            cwd=executable.parent,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                 "HOME": str(executable.parent)},
            user=nobody.pw_uid,
            group=nobody.pw_gid,
            extra_groups=[],
            start_new_session=True,
            close_fds=True,
            umask=0o077,
        )
        try:
            returncode = process.wait(timeout=RUN_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            returncode = None
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        if returncode != 0 or stdout.tell() > MAX_OUTPUT_BYTES:
            return None
        stdout.seek(0)
        return stdout.read()


@criterion
def behaviour(workspace: Path) -> bool:
    nobody = pwd.getpwnam("nobody")
    run_dir = Path(tempfile.mkdtemp(prefix="titlecase-run-"))
    try:
        executable = run_dir / "titlecase"
        build = subprocess.run(
            ["go", "build", "-o", str(executable), "."],
            cwd=workspace,
            env=GO_ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=300,
        )
        if build.returncode != 0:
            return False
        exams = [((DATA / i).read_bytes(), (DATA / e).read_bytes()) for i, e in EXAMS]
        _lock_down(workspace, nobody)
        os.chown(executable, nobody.pw_uid, nobody.pw_gid)
        executable.chmod(0o500)
        os.chown(run_dir, nobody.pw_uid, nobody.pw_gid)
        for inputs, expected in exams:
            actual = _run(executable, inputs, nobody)
            if actual is None or _lines(actual) != _lines(expected):
                return False
        return True
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
