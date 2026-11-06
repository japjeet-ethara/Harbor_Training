"""Share of hidden titles the Go program titlecases exactly."""

from pathlib import Path

from rewardkit import Worker, WorkerError, criterion

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _line_score(actual: str, expected: str) -> float:
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    if len(actual_lines) != len(expected_lines) or not expected_lines:
        return 0.0
    matched = sum(
        got == want for got, want in zip(actual_lines, expected_lines)
    )
    return matched / len(expected_lines)


@criterion
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0
    if not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    try:
        result = Worker(
            env={"PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"}
        ).run(
            f"cd {workspace.name} && go build -o titlecase . && ./titlecase",
            files=[workspace],
            stdin=HIDDEN_INPUTS.read_bytes(),
            timeout_sec=180,
        )
    except WorkerError:
        return 0.0
    try:
        actual = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return 0.0
    expected = HIDDEN_EXPECTED.read_text(encoding="utf-8")
    return _line_score(actual, expected)
