"""Share of hidden lines the built Go program titlecases exactly."""

import fcntl
import shlex
from contextlib import contextmanager
from pathlib import Path

from rewardkit import Worker, WorkerError, WorkerSetupError, criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
RUN_TIMEOUT_SEC = 120


@contextmanager
def go_lock():
    lock_path = Path("/tmp/rewardkit-go.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def line_score(stdout: bytes) -> float:
    try:
        actual = stdout.decode("utf-8").splitlines()
        expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return 0.0
    if not expected:
        return 0.0
    matched = sum(
        1
        for index, line in enumerate(expected)
        if index < len(actual) and actual[index] == line
    )
    return matched / len(expected)


@criterion
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir() or not HIDDEN_INPUTS.is_file():
        return 0.0
    folder = shlex.quote(workspace.name)
    script = f"""
set -eu
cd {folder}
if [ "$(go list -f '{{{{.Name}}}}' .)" = main ]; then
  go build -o "$HOME/titlecase" .
else
  dir=$(go list -f '{{{{if eq .Name "main"}}}}{{{{.Dir}}}}{{{{end}}}}' ./... | head -n 1)
  test -n "$dir"
  go build -o "$HOME/titlecase" "$dir"
fi
exec "$HOME/titlecase"
"""
    worker = Worker(
        env={
            "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
            "CGO_ENABLED": "0",
        }
    )
    try:
        with go_lock():
            result = worker.run(
                script,
                files=[workspace],
                stdin=HIDDEN_INPUTS.read_bytes(),
                timeout_sec=RUN_TIMEOUT_SEC,
            )
    except WorkerSetupError:
        raise
    except (OSError, WorkerError):
        return 0.0
    return line_score(result.stdout)
