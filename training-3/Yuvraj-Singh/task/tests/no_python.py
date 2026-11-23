"""No Python sources left behind, and the tree still builds."""

import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def _no_py_files(repo: Path) -> bool:
    """Ensure no *.py source files exist."""
    return not any(repo.rglob("*.py"))


def _no_python_shebangs(repo: Path) -> bool:
    """Reject any file whose first line contains the word 'python' (case-insensitive)."""
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        try:
            first = path.read_bytes()[:256]
            first_line = first.split(b"\n", 1)[0]
            if b"python" in first_line.lower():
                return False
        except (OSError, PermissionError):
            continue
    return True


def _no_python_names(repo: Path) -> bool:
    """Reject any file whose name matches python* or py_* regardless of extension."""
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.startswith("python") or name.startswith("py_"):
            return False
    return True


def _no_python_exec_in_go(repo: Path) -> bool:
    """Reject any .go file that shells out to a python interpreter."""
    PYTHON_CALLS = (
        b'"python"',
        b'"python3"',
        b'"python2"',
        b'`python`',
        b'`python3`',
        b"'python'",
        b"'python3'",
    )
    for path in repo.rglob("*.go"):
        try:
            src = path.read_bytes()
            for needle in PYTHON_CALLS:
                if needle in src:
                    return False
        except (OSError, PermissionError):
            continue
    return True


def _no_python_in_scripts(repo: Path) -> bool:
    """Reject any shell script that invokes python."""
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
            if b"python" in data.lower() and (
                path.suffix in (".sh", ".bash")
                or data[:2] == b"#!"
            ):
                return False
        except (OSError, PermissionError):
            continue
    return True


def _build_passes(repo: Path) -> bool:
    """Verify that go build ./... succeeds."""
    proc = subprocess.run(
        ["go", "build", "./..."],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.returncode == 0


@criterion
def no_python_files(workspace: Path) -> float:
    del workspace
    try:
        if not REPO.is_dir():
            return 0.0
        if not _no_py_files(REPO):
            return 0.0
        if not _no_python_shebangs(REPO):
            return 0.0
        if not _no_python_names(REPO):
            return 0.0
        if not _no_python_exec_in_go(REPO):
            return 0.0
        if not _no_python_in_scripts(REPO):
            return 0.0
        return 1.0 if _build_passes(REPO) else 0.0
    except Exception:
        return 0.0
