"""Offline Go builds and byte-for-byte comparisons for the verifier."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BUILD_TIMEOUT_SEC = 120


def build_port(workspace: Path, build_dir: Path, binary: Path) -> None:
    env = dict(
        os.environ,
        CGO_ENABLED="0",
        GOENV="off",
        GOFLAGS="-mod=readonly",
        GOMODCACHE=str(build_dir / "modules"),
        GOPROXY="off",
        GOSUMDB="off",
        GOTOOLCHAIN="local",
        GOWORK="off",
    )

    def go(*args: str) -> str:
        proc = subprocess.run(
            ["go", *args],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT_SEC,
        )
        if proc.returncode:
            detail = (proc.stderr or proc.stdout).strip()[-2000:]
            raise RuntimeError(f"go {args[0]} failed: {detail}")
        return proc.stdout

    mod = json.loads(go("mod", "edit", "-json"))
    if mod.get("Require") or mod.get("Replace"):
        raise RuntimeError("the Go module must use only the standard library")
    go("build", "-o", str(build_dir) + "/", "./...")
    go("build", "-o", str(binary), ".")


def compare_lines(expected: bytes, actual: bytes) -> tuple[int, int]:
    """Compare every byte per LF-delimited record and count extra or absent lines."""
    expected_lines = expected.removesuffix(b"\n").split(b"\n")
    actual_lines = actual.removesuffix(b"\n").split(b"\n") if actual else []
    correct = sum(want == got for want, got in zip(expected_lines, actual_lines))
    return correct, max(len(expected_lines), len(actual_lines))
