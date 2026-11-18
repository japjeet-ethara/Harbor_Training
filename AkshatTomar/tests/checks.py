"""Reward Kit checks for the titlecase Go port."""

import subprocess
import threading
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

_GO_LOCK = threading.Lock()
_HIDDEN_INPUT = Path("/tests/data/hidden_inputs.txt")
_HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
_BUILD_TIMEOUT_SEC = 180
_RUN_TIMEOUT_SEC = 60


def _go(workspace: Path, args: list[str], timeout: int) -> subprocess.CompletedProcess[bytes] | None:
    if not workspace.is_dir():
        return None
    try:
        with _GO_LOCK:
            return subprocess.run(
                ["go", *args],
                cwd=workspace,
                capture_output=True,
                timeout=timeout,
            )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _build_ok(workspace: Path) -> bool:
    result = _go(workspace, ["build", "./..."], _BUILD_TIMEOUT_SEC)
    return result is not None and result.returncode == 0


def _python_files(workspace: Path) -> bool:
    if not workspace.is_dir():
        return True
    return any(path.is_file() for path in workspace.rglob("*.py"))


def _split_lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    if data == b"":
        return []
    return data.split(b"\n")


def _main_dirs(workspace: Path) -> list[Path]:
    result = _go(
        workspace,
        ["list", "-f", "{{if eq .Name \"main\"}}{{.Dir}}{{end}}", "./..."],
        _BUILD_TIMEOUT_SEC,
    )
    if result is None or result.returncode != 0:
        return []
    return [Path(line.decode()) for line in result.stdout.splitlines() if line.strip()]


def _choose_main(workspace: Path, dirs: list[Path]) -> Path | None:
    if not dirs:
        return None
    root = workspace.resolve()
    for directory in dirs:
        if directory.resolve() == root:
            return directory
    if len(dirs) == 1:
        return dirs[0]
    return sorted(dirs, key=lambda directory: (len(directory.parts), str(directory)))[0]


def _line_fraction(expected: bytes, actual: bytes) -> float:
    expected_lines = _split_lines(expected)
    actual_lines = _split_lines(actual)
    total = max(len(expected_lines), len(actual_lines))
    if total == 0:
        return 1.0
    matches = sum(left == right for left, right in zip(expected_lines, actual_lines))
    return matches / total


@criterion
def build(workspace: Path) -> bool:
    return _build_ok(workspace)


@criterion
def no_python(workspace: Path) -> bool:
    return _build_ok(workspace) and not _python_files(workspace)


@criterion
def behaviour(workspace: Path) -> float:
    if not _build_ok(workspace):
        return 0.0
    if not _HIDDEN_INPUT.is_file() or not _HIDDEN_EXPECTED.is_file():
        return 0.0
    main_dir = _choose_main(workspace, _main_dirs(workspace))
    if main_dir is None:
        return 0.0
    binary = Path(f"/tmp/titlecase-behaviour-{threading.get_ident()}")
    built = _go(main_dir, ["build", "-o", str(binary), "."], _BUILD_TIMEOUT_SEC)
    if built is None or built.returncode != 0 or not binary.is_file():
        return 0.0
    try:
        with _HIDDEN_INPUT.open("rb") as source:
            ran = subprocess.run(
                [str(binary)],
                stdin=source,
                capture_output=True,
                timeout=_RUN_TIMEOUT_SEC,
            )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    return _line_fraction(_HIDDEN_EXPECTED.read_bytes(), ran.stdout)


rk.build(weight=1)
rk.no_python(weight=1)
rk.behaviour(weight=4)
