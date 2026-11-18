"""Shared Go invocations for the verifier checks."""

import os
import subprocess
import tempfile
from pathlib import Path


def build_all(workspace: Path) -> bool:
    return _run(workspace, ["go", "build", "./..."])


def build_program(workspace: Path, output: Path) -> bool:
    return _run(workspace, ["go", "build", "-o", os.fspath(output), "."])


def _run(workspace: Path, args: list[str]) -> bool:
    if not workspace.is_dir():
        return False
    with tempfile.TemporaryDirectory(prefix="go-build-") as tmp:
        root = Path(tmp)
        (root / "tmp").mkdir()
        env = os.environ.copy()
        env["GOCACHE"] = str(root / "cache")
        env["GOPATH"] = str(root / "gopath")
        env["GOTMPDIR"] = str(root / "tmp")
        try:
            result = subprocess.run(
                args,
                cwd=workspace,
                env=env,
                capture_output=True,
                timeout=180,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0
