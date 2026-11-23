"""Score the share of hidden titles the Go program titlecases exactly."""

import shlex
from pathlib import Path

from rewardkit import Worker, WorkerError, criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def lines(text: str) -> list[str]:
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


@criterion
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    expected = lines(HIDDEN_EXPECTED.read_text(encoding="utf-8"))
    if not expected:
        return 0.0
    script = (
        f"cd {shlex.quote(workspace.name)} && go build ./... && "
        "go build -o titlecase.bin . && exec ./titlecase.bin"
    )
    try:
        result = Worker(
            env={
                "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
                "GOTOOLCHAIN": "local",
                "GOPROXY": "off",
                "GOFLAGS": "-mod=readonly",
            }
        ).run(
            script,
            files=[workspace],
            stdin=HIDDEN_INPUTS.read_bytes(),
            timeout_sec=180,
        )
    except WorkerError:
        return 0.0
    try:
        observed = lines(result.stdout.decode("utf-8"))
    except UnicodeDecodeError:
        return 0.0
    total = max(len(expected), len(observed))
    matched = sum(
        i < len(observed) and observed[i] == expected[i] for i in range(len(expected))
    )
    return matched / total
