"""Check B: no Python source remains and the repository still compiles."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import describe_build, go_build  # noqa: E402
from rewardkit.session import criterion  # noqa: E402


@criterion(description="Check that no .py files remain and `go build ./...` still succeeds")
def no_python(workspace: Path) -> dict:
    if not workspace.is_dir():
        return {"score": 0.0, "reasoning": f"workspace is missing: {workspace}"}

    try:
        py_files = sorted(
            path.relative_to(workspace).as_posix()
            for path in workspace.rglob("*.py")
            if path.is_file()
        )
    except OSError as exc:
        return {"score": 0.0, "reasoning": f"could not scan workspace for .py files: {exc}"}

    try:
        proc = go_build(workspace)
    except Exception as exc:  # noqa: BLE001 - explicit failure reporting
        return {"score": 0.0, "reasoning": f"could not run go build: {exc}"}

    build_description = describe_build(proc)
    if py_files:
        shown = ", ".join(py_files[:10])
        if len(py_files) > 10:
            shown += f", ... ({len(py_files) - 10} more)"
        return {
            "score": 0.0,
            "reasoning": f"{len(py_files)} .py file(s) remain: {shown}; {build_description}",
        }
    if proc.returncode != 0:
        return {"score": 0.0, "reasoning": f"no .py files remain, but {build_description}"}
    return {
        "score": 1.0,
        "reasoning": f"no .py files remain and {build_description}",
    }
