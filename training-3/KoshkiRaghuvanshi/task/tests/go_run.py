"""Run the submitted module in a Reward Kit worker."""

import shlex
from pathlib import Path

from rewardkit import Worker, WorkerError, WorkerResult

GO_ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "CGO_ENABLED": "0",
    "GOTOOLCHAIN": "local",
}
BUILD_TIMEOUT_SEC = 300


def go(workspace: Path, script: str, stdin: bytes = b"") -> WorkerResult | None:
    """Copy the workspace in and run script. None means the run did not finish."""
    quoted = shlex.quote(workspace.name)
    try:
        return Worker(env=GO_ENV).run(
            f"cd {quoted} && {script}",
            files=[workspace],
            stdin=stdin,
            timeout_sec=BUILD_TIMEOUT_SEC,
        )
    except WorkerError:
        return None
