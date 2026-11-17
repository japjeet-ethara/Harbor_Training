"""Score the share of hidden lines that match the original titlecase() answers."""

import shutil
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
BINARY = Path("/tmp/tc")
HIDDEN_IN = Path("/tests/data/hidden_inputs.txt")
HIDDEN_OUT = Path("/tests/data/hidden_expected.txt")


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _score(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 0.0
    matches = sum(
        1 for i, exp in enumerate(expected) if i < len(actual) and actual[i] == exp
    )
    return matches / len(expected)


@criterion
def hidden_behavior(workspace: Path) -> float:
    del workspace
    try:
        if not REPO.is_dir() or not HIDDEN_IN.is_file() or not HIDDEN_OUT.is_file():
            return 0.0
        expected = HIDDEN_OUT.read_text(encoding="utf-8").splitlines()
        _remove(BINARY)
        build = subprocess.run(
            ["go", "build", "-o", str(BINARY), "."],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if build.returncode != 0 or not BINARY.is_file():
            return _score(expected, [])
        proc = subprocess.run(
            [str(BINARY)],
            input=HIDDEN_IN.read_bytes(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        actual = proc.stdout.decode("utf-8", errors="replace").splitlines()
        return _score(expected, actual)
    except Exception:
        return 0.0
