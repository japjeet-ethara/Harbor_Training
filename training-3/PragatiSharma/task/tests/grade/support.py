"""Shared Go grading helpers. This module registers no Reward Kit criteria."""

import subprocess
import sys
from pathlib import Path

BUILD_TIMEOUT_SEC = 60
RUN_TIMEOUT_SEC = 60
# Records in the graded exam, tests/data/inputs.txt and tests/data/answers.txt
# (frozen with kit/answers.py; kit/report.txt: 100000 kept, 0 dropped).
EXAM_RECORD_COUNT = 100000

# The submitted program runs as this unprivileged user, never as root.
# tests/Dockerfile makes /tests and the Python interpreter root-only and checks
# that this UID can use neither. Keep the two numbers in sync.
SUBMISSION_UID = 40000
SUBMISSION_ENV = {"PATH": "/usr/bin:/bin"}


def log(message: str) -> None:
    print(message, file=sys.stderr)


def records(data: bytes) -> list[bytes]:
    """Split on LF only. Keep spaces and blank lines. Drop one trailing LF."""
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


def run_command(
    args: list[str],
    cwd: Path,
    timeout: int,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int | None, bytes, bytes, bool]:
    """Run a command. Stdout and stderr stay separate. A timeout is not an exception."""
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
        stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
        return None, stdout, stderr, True
    except OSError as exc:
        return None, b"", str(exc).encode(), False
    return completed.returncode, completed.stdout, completed.stderr, False


def as_submission_user(args: list[str]) -> list[str]:
    """Run ``args`` as SUBMISSION_UID with no groups and no way back to root."""
    return [
        "/usr/bin/setpriv",
        f"--reuid={SUBMISSION_UID}",
        f"--regid={SUBMISSION_UID}",
        "--clear-groups",
        "--no-new-privs",
        "--",
        *args,
    ]


def run_submission(
    binary: Path, stdin: bytes, timeout: int
) -> tuple[int | None, bytes, bytes, bool]:
    """Run the built program as SUBMISSION_UID from the binary's own folder.

    Afterwards, kill every process that UID still owns, so nothing the program
    started keeps running while the grader finishes.
    """
    binary.parent.chmod(0o711)
    binary.chmod(0o755)
    try:
        return run_command(
            as_submission_user([str(binary)]),
            binary.parent,
            timeout,
            stdin=stdin,
            env=SUBMISSION_ENV,
        )
    finally:
        subprocess.run(
            as_submission_user(["/bin/sh", "-c", "kill -KILL -1"]),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=SUBMISSION_ENV,
            check=False,
        )


def python_files(workspace: Path) -> list[Path]:
    return sorted(
        path for path in workspace.rglob("*") if path.is_file() and path.suffix == ".py"
    )


def go_build_all(workspace: Path) -> tuple[bool, str]:
    if not workspace.is_dir():
        return False, f"workspace is not a directory: {workspace}"
    code, _stdout, stderr, timed_out = run_command(
        ["go", "build", "./..."],
        workspace,
        BUILD_TIMEOUT_SEC,
    )
    if timed_out:
        return False, f"go build ./... timed out after {BUILD_TIMEOUT_SEC}s"
    if code != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        return False, detail or f"go build ./... exited {code}"
    return True, "go build ./... succeeded"
