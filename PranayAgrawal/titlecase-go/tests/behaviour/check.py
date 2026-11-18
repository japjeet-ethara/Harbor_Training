"""Behaviour check: run the submitted Go program on the hidden fixtures."""

from pathlib import Path
import subprocess
import tempfile

from rewardkit import criterion

BUILD_TIMEOUT_SEC = 300
RUN_TIMEOUT_SEC = 180

DATA_DIR = Path("/tests/data")
if not DATA_DIR.is_dir():
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _run(args: list[str], cwd: Path, timeout: int, stdin_bytes: bytes | None = None):
    kwargs = {
        "cwd": str(cwd),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "timeout": timeout,
        "check": False,
    }
    if stdin_bytes is None:
        kwargs["stdin"] = subprocess.DEVNULL
    else:
        kwargs["input"] = stdin_bytes
    return subprocess.run(args, **kwargs)


def _main_packages(workspace: Path) -> list[str]:
    try:
        completed = _run(
            ["go", "list", "-f", '{{if eq .Name "main"}}{{.Dir}}{{end}}', "./..."],
            workspace,
            BUILD_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    output = completed.stdout.decode("utf-8", "replace")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _build_binary(workspace: Path, binary: Path) -> bool:
    # The expected layout is a main package at the repository root.
    try:
        completed = _run(
            ["go", "build", "-o", str(binary), "."],
            workspace,
            BUILD_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        completed = None
    if completed is not None and completed.returncode == 0 and binary.is_file():
        return True

    # Fall back to a single main package elsewhere in the module.  If there
    # are several, prefer the shallowest, which is the least surprising one.
    packages = _main_packages(workspace)
    if not packages:
        return False

    workspace_resolved = workspace.resolve()

    def sort_key(directory: str):
        path = Path(directory)
        try:
            relative = path.resolve().relative_to(workspace_resolved)
        except (OSError, ValueError):
            relative = path
        return (len(relative.parts), str(relative))

    package = sorted(packages, key=sort_key)[0]
    try:
        completed = _run(
            ["go", "build", "-o", str(binary), package],
            workspace,
            BUILD_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0 and binary.is_file()


def _read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _accuracy(workspace: Path) -> float:
    inputs_path = DATA_DIR / "hidden_inputs.txt"
    expected_path = DATA_DIR / "hidden_expected.txt"
    try:
        stdin_bytes = inputs_path.read_bytes()
        expected = _read_lines(expected_path)
    except OSError:
        return 0.0

    if not expected:
        return 0.0

    with tempfile.TemporaryDirectory(prefix="titlecase-behaviour-") as tmp:
        binary = Path(tmp) / "titlecase-under-test"
        if not _build_binary(workspace, binary):
            return 0.0
        try:
            binary.chmod(0o755)
        except OSError:
            pass
        try:
            completed = _run(
                [str(binary)],
                workspace,
                RUN_TIMEOUT_SEC,
                stdin_bytes,
            )
        except (OSError, subprocess.TimeoutExpired):
            return 0.0

        actual = completed.stdout.decode("utf-8", "replace").split("\n")
        if actual and actual[-1] == "":
            actual.pop()

        matches = sum(1 for got, want in zip(actual, expected) if got == want)
        return matches / len(expected)


@criterion
def hidden_fixture_accuracy(workspace: Path) -> float:
    try:
        return _accuracy(workspace)
    except Exception:
        return 0.0
