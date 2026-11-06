"""Trusted helpers for the titlecase verifier. This file registers no criteria."""

from __future__ import annotations

import shlex
from pathlib import Path

GO_ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "GOROOT": "/usr/local/go",
    "GO111MODULE": "on",
    "GOPROXY": "off",
    "GOSUMDB": "off",
    "CGO_ENABLED": "0",
    "GOFLAGS": "-mod=readonly",
}

DATASETS = Path("/tests/datasets")
VISIBLE_INPUT = DATASETS / "visible_input.txt"
VISIBLE_EXPECTED = DATASETS / "visible_expected.txt"
HIDDEN_INPUT = DATASETS / "hidden_input.txt"
HIDDEN_EXPECTED = DATASETS / "hidden_expected.txt"


def module_dir_name(workspace: Path) -> str:
    if not workspace.is_dir():
        raise ValueError("workspace is not a directory")
    name = workspace.name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("workspace directory name is not usable")
    return name


def build_command(workspace: Path) -> str:
    module = shlex.quote(module_dir_name(workspace))
    return f"cd {module} && go build ./..."


def run_command(workspace: Path) -> str:
    module = shlex.quote(module_dir_name(workspace))
    return f"cd {module} && go build -o titlecase-bin ./... && ./titlecase-bin"


def contains_python_file(workspace: Path) -> bool:
    if not workspace.is_dir():
        return True
    for path in workspace.rglob("*"):
        if path.is_symlink():
            return True
        if path.name.endswith(".py"):
            return True
    return False


def require_dataset(path: Path) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"verifier dataset is missing: {path}")
    return path.read_bytes()


def stdout_matches(stdout: bytes, expected_path: Path) -> bool:
    return stdout == require_dataset(expected_path)
