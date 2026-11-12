"""Programmatic criteria for the titlecase-go task.

Three checks are registered, combined with weights 1 : 1 : 10:

``build``      ``go build ./...`` succeeds in the workspace.
``no_python``  no ``.py`` file remains anywhere in the repository *and* the
               build succeeds.
``behaviour``  the program built from the workspace reproduces the hidden
               expected title-casing, scored as the share of matching lines.

Reward Kit passes the workspace path (``/workspace/repo``, see
``test.sh``) to every criterion.  The hidden fixtures are bundled in
``data/`` beside this file, so they never exist in the agent's container.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from rewardkit import criteria, criterion

DATA_DIR = Path(__file__).resolve().parent / "data"
BUILD_TIMEOUT_SEC = 300
RUN_TIMEOUT_SEC = 120


def _run(
    args: list[str],
    cwd: Path,
    *,
    timeout: int = BUILD_TIMEOUT_SEC,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run *args* in *cwd* without shell interpolation."""
    return subprocess.run(
        args,
        cwd=str(cwd),
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _build_passes(workspace: Path) -> bool:
    """True when ``go build ./...`` exits 0 in *workspace*."""
    if not workspace.is_dir():
        return False
    try:
        result = _run(["go", "build", "./..."], workspace)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _split_lf(text: str) -> list[str]:
    """Split on LF only and drop the single trailing newline."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _main_package(workspace: Path) -> str | None:
    """Return the import path of the main package to run, if any."""
    try:
        root = _run(["go", "list", "-f", "{{.Name}}", "."], workspace, timeout=60)
        if root.returncode == 0 and root.stdout.decode().strip() == "main":
            return "."

        listing = _run(
            [
                "go",
                "list",
                "-f",
                '{{if eq .Name "main"}}{{.ImportPath}}{{end}}',
                "./...",
            ],
            workspace,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if listing.returncode != 0:
        return None
    mains = [line.strip() for line in listing.stdout.decode().splitlines() if line.strip()]
    return mains[0] if mains else None


@criterion(description="`go build ./...` succeeds in /workspace/repo")
def build(workspace: Path) -> bool:
    return _build_passes(workspace)


@criterion(description="No .py files remain and `go build ./...` succeeds")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return False
    return _build_passes(workspace)


@criterion(description="Share of hidden inputs reproduced exactly")
def behaviour(workspace: Path) -> float:
    inputs_path = DATA_DIR / "hidden_inputs.txt"
    expected_path = DATA_DIR / "hidden_expected.txt"
    if not workspace.is_dir() or not inputs_path.is_file() or not expected_path.is_file():
        return 0.0

    expected = _split_lf(expected_path.read_text(encoding="utf-8"))
    if not expected:
        return 0.0

    package = _main_package(workspace)
    if package is None:
        return 0.0

    try:
        with tempfile.TemporaryDirectory(prefix="titlecase-go-") as tmp:
            binary = Path(tmp) / "titlecase-go"
            compiled = _run(["go", "build", "-o", str(binary), package], workspace)
            if compiled.returncode != 0 or not binary.is_file():
                return 0.0

            run = _run(
                [str(binary)],
                workspace,
                timeout=RUN_TIMEOUT_SEC,
                stdin=inputs_path.read_bytes(),
            )
    except (OSError, subprocess.SubprocessError):
        return 0.0

    output = _split_lf(run.stdout.decode("utf-8", errors="replace"))
    matched = sum(
        1
        for index, want in enumerate(expected)
        if index < len(output) and output[index] == want
    )
    return matched / len(expected)


# Register the checks (and fix their weights).  Without an explicit call the
# decorator would register each one with the default weight of 1.0.
criteria.build(weight=1.0)
criteria.no_python(weight=1.0)
criteria.behaviour(weight=10.0)
