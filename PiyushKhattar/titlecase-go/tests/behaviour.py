from pathlib import Path

from rewardkit import Worker, WorkerError, criterion

_HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
_HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
_GO_ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "GOROOT": "/usr/local/go",
    "CGO_ENABLED": "0",
    # The worker directory is under /run, where Go ignores go.mod.
    # The program uses only the standard library, so GOPATH mode builds it.
    "GO111MODULE": "off",
}


def _lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


@criterion
def behaviour(workspace: Path) -> float:
    try:
        expected = _lines(_HIDDEN_EXPECTED.read_bytes())
        stdin = _HIDDEN_INPUTS.read_bytes()
    except OSError:
        return 0.0
    if not expected:
        return 0.0
    files = [path for path in workspace.iterdir()] if workspace.is_dir() else []
    try:
        result = Worker(env=_GO_ENV).run(
            "go build -o titlecase-bin . && exec ./titlecase-bin",
            files=files,
            stdin=stdin,
            timeout_sec=120,
        )
    except WorkerError:
        return 0.0
    actual = _lines(result.stdout)
    matches = sum(
        1 for index, line in enumerate(expected) if index < len(actual) and actual[index] == line
    )
    return matches / len(expected)
