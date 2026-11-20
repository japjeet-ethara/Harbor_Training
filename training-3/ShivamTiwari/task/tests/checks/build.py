"""Build criterion with a correctness gate.

The build point is only awarded when the submitted module compiles *and* the
resulting binary reproduces at least 98% of the hidden exam.  A stub that merely
compiles therefore earns nothing.
"""

import os
import pwd
import subprocess
from pathlib import Path

from rewardkit import criterion

DATA = Path("/tests/data")
BIN = Path("/tmp/tc_build_bin")
MIN_ACCURACY = 0.98


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
    try:
        inputs = (DATA / "inputs.txt").read_bytes()
        expected = (DATA / "answers.txt").read_bytes()
        pw = pwd.getpwnam("runner")
        env = {
            "PATH": "/usr/local/go/bin:/usr/bin:/bin",
            "HOME": pw.pw_dir,
            "CGO_ENABLED": "0",
        }
        run = subprocess.run(
            [str(BIN)],
            cwd="/tmp",
            user=pw.pw_uid,
            group=pw.pw_gid,
            input=inputs,
            capture_output=True,
            timeout=300,
            env=env,
        )
    except Exception:
        return None
    finally:
        BIN.unlink(missing_ok=True)
    if run.returncode != 0:
        return None
    return _accuracy(run.stdout, expected)


@criterion(description="go build ./... succeeds and the binary matches the hidden exam")
def build(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
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
