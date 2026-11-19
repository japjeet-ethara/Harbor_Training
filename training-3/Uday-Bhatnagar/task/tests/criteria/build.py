"""Check A: the submitted repository compiles with ``go build ./...``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import describe_build, go_build  # noqa: E402
from rewardkit.session import criterion  # noqa: E402


@criterion(description="Check that `go build ./...` succeeds in the submitted repository")
def build(workspace: Path) -> dict:
    if not workspace.is_dir():
        return {"score": 0.0, "reasoning": f"workspace is missing: {workspace}"}
    try:
        proc = go_build(workspace)
    except Exception as exc:  # noqa: BLE001 - explicit failure reporting
        return {"score": 0.0, "reasoning": f"could not run go build: {exc}"}
    if proc.returncode == 0:
        return {"score": 1.0, "reasoning": describe_build(proc)}
    return {"score": 0.0, "reasoning": describe_build(proc)}
