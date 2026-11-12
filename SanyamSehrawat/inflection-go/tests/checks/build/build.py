"""build (weight 1): the repository builds with the image's Go toolchain, offline.

GOPROXY=off, GOTOOLCHAIN=local and CGO_ENABLED=0 mean nothing can be downloaded, a
go.mod asking for a newer Go fails, and C code cannot be compiled. A go.mod with a
require or replace line fails too, because the rules allow the standard library
only. Third-party source pasted into the repository as a local package cannot be
told apart from the agent's own code and is not detected.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {
    **os.environ,
    "GOFLAGS": "-mod=mod -buildvcs=false",
    "GOPROXY": "off",
    "GOTOOLCHAIN": "local",
    "CGO_ENABLED": "0",
}


def go(args, workspace):
    return subprocess.run(["go", *args], cwd=workspace, env=GO_ENV, capture_output=True, timeout=300).returncode == 0


def standard_library_only(workspace):
    text = (workspace / "go.mod").read_text(encoding="utf-8", errors="replace")
    return re.search(r"^\s*(require|replace)\b", text, re.MULTILINE) is None


@criterion(description="`go build ./...` passes and the root package builds into the program")
def build(workspace: Path) -> float:
    try:
        if not (workspace / "go.mod").is_file() or not standard_library_only(workspace):
            return 0.0
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "inflection"
            ok = go(["build", "./..."], workspace) and go(["build", "-o", str(exe), "."], workspace) and exe.is_file()
        return 1.0 if ok else 0.0
    except Exception:
        return 0.0
