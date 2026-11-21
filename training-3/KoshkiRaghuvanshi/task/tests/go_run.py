"""Run the submitted module in a Reward Kit worker."""

import shlex
import sys
from pathlib import Path

from rewardkit import Worker, WorkerError, WorkerResult

GO_ENV = {
    "PATH": "/usr/local/go/bin:/usr/bin:/bin",
    "CGO_ENABLED": "0",
    "GOTOOLCHAIN": "local",
}
BUILD_TIMEOUT_SEC = 300


def go(workspace: Path, script: str, stdin: bytes = b"") -> WorkerResult | None:
    """Copy the workspace in and run script. None means the run did not finish."""
    quoted = shlex.quote(workspace.name)
    cmd = (
        "WORKROOT=$(mktemp -d /tmp/go-work.XXXXXX) && "
        'export HOME="$WORKROOT" GOPATH="$WORKROOT/gopath" GOCACHE="$WORKROOT/gocache" && '
        'mkdir -p "$GOPATH" "$GOCACHE" && '
        f'cp -r {quoted} "$WORKROOT/" && '
        f'cd "$WORKROOT/{quoted}" && '
        f"{script}"
    )
    try:
        res = Worker(
            env=GO_ENV,
            private_paths=(
                Path("/tests"),
                Path("/logs/verifier"),
                Path("/usr/local/bin"),
            ),
        ).run(
            cmd,
            files=[workspace],
            stdin=stdin,
            timeout_sec=BUILD_TIMEOUT_SEC,
        )
        if res.returncode != 0:
            print(
                f"[DEBUG go()] rc={res.returncode} stdout={res.stdout[:300]!r} stderr={res.stderr[:500]!r}",
                file=sys.stderr,
            )
        return res
    except WorkerError as e:
        print(f"[DEBUG go()] WorkerError: {e}", file=sys.stderr)
        return None


def passes_behaviour(workspace: Path) -> bool:
    data = Path(__file__).resolve().parent / "data"
    try:
        stdin = (data / "inputs.txt").read_bytes()
        expected = (data / "answers.txt").read_bytes()
    except OSError as e:
        print(f"[DEBUG data] {e}", file=sys.stderr)
        return False
    if not expected:
        return False
    result = go(workspace, "go build -o titlecase.bin . && ./titlecase.bin", stdin)
    if result is None or result.returncode != 0:
        return False
    if result.stdout != expected:
        for idx, (a, b) in enumerate(zip(result.stdout, expected)):
            if a != b:
                line_no = result.stdout[:idx].count(b"\n") + 1
                print(
                    f"[DEBUG mismatch] line={line_no} byte={idx}: got={a!r} expected={b!r} got_len={len(result.stdout)} exp_len={len(expected)}",
                    file=sys.stderr,
                )
                break
        return False
    return True