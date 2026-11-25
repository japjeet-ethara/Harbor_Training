"""Behavior score above the identity-output baseline.

Builds are staged and run as nobody with no module downloads and cgo disabled.
The candidate still shares the verifier container. Process-group cleanup cannot
guarantee termination of a descendant that deliberately creates a new session.
"""

import os
import tempfile
from pathlib import Path

from rewardkit.session import criterion

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_support import run_unprivileged_go_build
from process_supervisor import (
    SupervisorCleanupError,
    SupervisorError,
    run_supervised_process,
)


HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
MAX_OUTPUT_BYTES = 1 << 20
CANDIDATE_GOMEMLIMIT = "768MiB"
CANDIDATE_TIMEOUT_SEC = 120


def _records(data: bytes, *, allow_crlf: bool = False) -> list[bytes]:
    """Parse LF records; input may use CRLF transport."""
    if data == b"":
        return []
    if not data.endswith(b"\n"):
        raise ValueError("record stream is missing its final LF")
    records = data[:-1].split(b"\n")
    if allow_crlf:
        records = [r[:-1] if r.endswith(b"\r") else r for r in records]
    if any(b"\r" in r for r in records):
        raise ValueError("bare or embedded CR")
    for record in records:
        record.decode("utf-8", errors="strict")
    return records


def _score(input_bytes: bytes, expected_bytes: bytes, output_bytes: bytes) -> float:
    """Reject malformed framing; normalize exact accuracy above identity."""
    try:
        inputs = _records(input_bytes, allow_crlf=True)
        expected = _records(expected_bytes)
        actual = _records(output_bytes)
    except (UnicodeDecodeError, ValueError):
        return 0.0
    if len(inputs) != len(expected) or len(actual) != len(expected):
        return 0.0
    if not inputs:
        return 1.0 if actual == expected == [] else 0.0
    raw = sum(a == e for a, e in zip(actual, expected)) / len(expected)
    echo = sum(i == e for i, e in zip(inputs, expected)) / len(expected)
    if echo >= 1.0:
        return 0.0
    return max(0.0, min(1.0, (raw - echo) / (1.0 - echo)))


def _limit_candidate() -> None:
    try:
        import resource
    except ImportError as exc:
        raise RuntimeError("candidate resource limits require Unix") from exc
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    file_limit = MAX_OUTPUT_BYTES + 1
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _candidate_environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": "/nonexistent",
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "GOMEMLIMIT": CANDIDATE_GOMEMLIMIT,
    }


def _run_candidate(executable: Path, input_bytes: bytes, cwd: Path,
                   timeout: int = CANDIDATE_TIMEOUT_SEC):
    """Run with file-backed stdio under subreaper supervision."""
    with tempfile.TemporaryFile(mode="w+b") as input_file, \
            tempfile.TemporaryFile(mode="w+b") as stdout_file, \
            tempfile.TemporaryFile(mode="w+b") as stderr_file:
        input_file.write(input_bytes)
        input_file.seek(0)
        try:
            returncode = run_supervised_process(
                [str(executable)], timeout=timeout,
                stdin=input_file, stdout=stdout_file,
                stderr=stderr_file, cwd=cwd,
                env=_candidate_environment(),
                user="nobody", group="nogroup", extra_groups=(),
                preexec_fn=_limit_candidate,
            )
            if returncode is None or returncode != 0:
                return None
        except SupervisorCleanupError:
            raise
        except (OSError, SupervisorError, RuntimeError):
            return None

        stdout_file.seek(0, os.SEEK_END)
        stderr_file.seek(0, os.SEEK_END)
        if stdout_file.tell() > MAX_OUTPUT_BYTES or stderr_file.tell() > MAX_OUTPUT_BYTES:
            return None
        stdout_file.seek(0)
        return stdout_file.read(MAX_OUTPUT_BYTES + 1)


@criterion(description="Behavioral accuracy above the identity-output baseline")
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    try:
        if any(p.is_file() and p.suffix == ".py" for p in workspace.rglob("*")):
            return 0.0
        input_bytes = HIDDEN_INPUTS.read_bytes()
        expected_bytes = HIDDEN_EXPECTED.read_bytes()
        if len(_records(input_bytes, allow_crlf=True)) != len(_records(expected_bytes)):
            return 0.0
    except (OSError, UnicodeDecodeError, ValueError):
        return 0.0

    with tempfile.TemporaryDirectory(prefix="titlecase-candidate-") as temp:
        temp_dir = Path(temp)
        binary = temp_dir / "titlecase"
        try:
            os.chmod(temp_dir, 0o755)
            if not run_unprivileged_go_build(workspace, output_binary=binary):
                return 0.0
            os.chmod(temp_dir, 0o555)
            output = _run_candidate(binary, input_bytes, temp_dir)
        except OSError:
            return 0.0
        if output is None:
            return 0.0
        return _score(input_bytes, expected_bytes, output)
