"""Shared helpers for the three checks (not a check itself: it has no criteria)."""
import os
import subprocess
from pathlib import Path

REPO = Path("/workspace/repo")
ENV = {
    **os.environ,
    "GOTOOLCHAIN": "local",   # never download another Go version
    "GOPROXY": "off",         # standard library only: no module downloads
    "GOFLAGS": "-mod=readonly",
    "CGO_ENABLED": "0",
}


def run(cmd, cwd=REPO, timeout=300, stdin=None):
    try:
        return subprocess.run(cmd, cwd=str(cwd), env=ENV, capture_output=True,
                              timeout=timeout, input=stdin)
    except (subprocess.TimeoutExpired, OSError):
        return None


def build_binary(out_path):
    """Build the main package that lives in the repository root. True on success."""
    p = run(["go", "build", "-o", str(out_path), "."])
    return p is not None and p.returncode == 0 and Path(out_path).is_file()


def build_all():
    p = run(["go", "build", "./..."])
    return p is not None and p.returncode == 0
