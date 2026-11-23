"""Check 2: no Python source code remains, no external Python launcher wrappers,
and the Go build passes.
"""

import subprocess
import tempfile
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn=None, **kwargs):
        if fn is None:
            return lambda f: f
        return fn

PYTHON_SOURCE_PATTERNS = [
    b"import sys",
    b"import os",
    b"def titlecase(",
    b"def _",
    b"#!/usr/bin/env python",
    b"#!/bin/python",
]

ALLOWED_TEXT_EXTS = {".go", ".mod", ".sum", ".md", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".gitignore", ".gitattributes"}


@criterion(description="no Python source code anywhere in the repository and genuine Go build")
def no_python_left(workspace: Path) -> bool:
    # 1. No files ending in .py anywhere (case-insensitive)
    for p in workspace.rglob("*"):
        if p.is_file() and p.name.lower().endswith(".py"):
            return False

    if not (workspace / "go.mod").is_file():
        return False

    # 2. Prevent cloaked Python source files (e.g. reference.txt, titlecase_src.txt)
    for p in workspace.rglob("*"):
        if p.is_file():
            # Skip compiled executables / binaries
            if p.suffix.lower() in [".exe", ""]:
                continue
            try:
                content = p.read_bytes()
                if any(pat in content for pat in PYTHON_SOURCE_PATTERNS):
                    return False
            except Exception:
                pass

    # 3. Check that Go source files do not import os/exec to launch Python
    for go_file in workspace.rglob("*.go"):
        try:
            content = go_file.read_text(encoding="utf-8", errors="replace")
            if '"os/exec"' in content and ("python" in content.lower() or "exec.Command" in content):
                return False
        except Exception:
            pass

    # 4. Genuine Go compilation check
    try:
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run(
                ["go", "build", "-o", out + "/", "./..."],
                cwd=workspace, capture_output=True, timeout=300,
            )
    except Exception:
        return False
    return result.returncode == 0
