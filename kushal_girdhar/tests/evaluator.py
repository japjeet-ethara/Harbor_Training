from dataclasses import dataclass
from functools import cache
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
GO = "/usr/local/go/bin/go"
UID = 65534


@dataclass(frozen=True)
class Result:
    build: bool = False
    no_python: bool = False
    behaviour: float = 0.0


def inspect_workspace(workspace):
    if not workspace.is_dir() or workspace.is_symlink():
        raise ValueError("workspace is missing or unsafe")
    python = False
    for parent, directories, files in os.walk(workspace, followlinks=False):
        for name in directories + files:
            mode = (Path(parent) / name).lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError("workspace contains an unsafe entry")
            if stat.S_ISREG(mode) and name.endswith(".py"):
                python = True
    return not python


def compare(actual, expected):
    if not actual.endswith(b"\n") or actual.count(b"\n") != expected.count(b"\n"):
        return 0.0
    want = expected.split(b"\n")[:-1]
    got = actual.split(b"\n")[:-1]
    matched = sum(a == b for a, b in zip(got, want, strict=True))
    return matched / len(want)


def candidate_environment(scratch):
    return {
        "PATH": "/usr/local/go/bin:/usr/bin:/bin",
        "HOME": str(scratch),
        "TMPDIR": str(scratch),
        "GOCACHE": str(scratch / "cache"),
        "GOMODCACHE": str(scratch / "modules"),
        "GOENV": "off",
        "GOWORK": "off",
        "GOTOOLCHAIN": "local",
        "GOPROXY": "off",
        "GOSUMDB": "off",
        "CGO_ENABLED": "0",
        "GOTELEMETRY": "off",
        "GOMAXPROCS": "2",
        "LANG": "C.UTF-8",
    }


def run(command, workspace, scratch, timeout, data=None):
    launcher = [sys.executable, "-I", str(HERE / "isolate.py")]
    with tempfile.TemporaryFile() as output:
        with subprocess.Popen(
            [*launcher, *command],
            cwd=workspace,
            env=candidate_environment(scratch),
            stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        ) as proc:
            try:
                proc.communicate(input=data, timeout=timeout)
                if proc.returncode != 0:
                    return None
                output.seek(0)
                return output.read()
            except subprocess.TimeoutExpired:
                return None
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def prepare_workspace(workspace, scratch):
    os.chown(scratch, UID, UID)
    os.chown(workspace, UID, UID)


@cache
def evaluate(workspace):
    try:
        python_free = inspect_workspace(workspace)
    except (OSError, ValueError):
        return Result()
    if not (workspace / "go.mod").is_file():
        return Result()
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes()
    if any(stream.count(b"\n") != 2000 or not stream.endswith(b"\n") for stream in (inputs, expected)):
        raise ValueError("invalid frozen data framing")
    with tempfile.TemporaryDirectory(prefix="titlecase-") as temp:
        scratch = Path(temp)
        prepare_workspace(workspace, scratch)
        if run([GO, "build", "./..."], workspace, scratch, 130) is None:
            return Result()
        binary = scratch / "titlecase"
        if run([GO, "build", "-o", str(binary), "."], workspace, scratch, 55) is None:
            return Result(True, python_free)
        actual = run([str(binary)], workspace, scratch, 75, inputs)
        return Result(True, python_free, compare(actual, expected) if actual is not None else 0.0)
