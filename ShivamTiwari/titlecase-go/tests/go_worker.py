"""Run the submitted module as an unprivileged worker."""

import shlex
from pathlib import Path

from rewardkit import Worker, WorkerError, WorkerResult


def run_go(workspace: Path, build_command: str, *, stdin: bytes = b"", run_binary: bool = False) -> WorkerResult:
    directory = shlex.quote(workspace.name)
    binary = "./titlecase" if run_binary else ""
    script = f"""
set -eu
cd {directory}
export GOCACHE="$HOME/gocache"
export GOMODCACHE="$HOME/modcache"
export GOPATH="$HOME/gopath"
export CGO_ENABLED=0
export GOTOOLCHAIN=local
mkdir -p "$GOCACHE" "$GOMODCACHE" "$GOPATH"
{build_command}
{binary}
"""
    return Worker().run(
        script,
        files=[workspace],
        stdin=stdin,
        timeout_sec=180,
    )


def run_go_or_fail(workspace: Path, build_command: str, *, stdin: bytes = b"", run_binary: bool = False) -> WorkerResult | None:
    if not workspace.is_dir():
        return None
    try:
        return run_go(workspace, build_command, stdin=stdin, run_binary=run_binary)
    except WorkerError:
        return None
