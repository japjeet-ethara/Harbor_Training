"""Shared command helpers. This module registers no reward criteria."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def go_build(workspace: Path, *args: str, timeout: int = 180) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["GO111MODULE"] = "on"
    env["GOCACHE"] = tempfile.mkdtemp(prefix="gocache-")
    env["GOPATH"] = tempfile.mkdtemp(prefix="gopath-")
    env.setdefault("CGO_ENABLED", "0")
    return subprocess.run(
        ["go", "build", *args],
        cwd=workspace,
        env=env,
        capture_output=True,
        timeout=timeout,
    )
