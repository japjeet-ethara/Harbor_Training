"""no_python (weight 1): no .py file is left in the repository AND the build passes.

The build condition matters: without it, an agent that only deletes files would
be paid for doing no porting at all. "The build passes" means the same as in the
build check.
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


def python_files(workspace):
    return [
        os.path.join(folder, name)
        for folder, _, names in os.walk(workspace)
        for name in names
        if name.endswith(".py")
    ]


@criterion(description="no .py file anywhere under the repository, and the Go build passes")
def no_python(workspace: Path) -> float:
    try:
        if not (workspace / "go.mod").is_file() or python_files(workspace):
            return 0.0
        if not standard_library_only(workspace):
            return 0.0
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "titlecase"
            ok = go(["build", "./..."], workspace) and go(["build", "-o", str(exe), "."], workspace) and exe.is_file()
        return 1.0 if ok else 0.0
    except Exception:
        return 0.0
