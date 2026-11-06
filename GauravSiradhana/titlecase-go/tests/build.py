"""Build check: go build ./... passes and the module stays on the standard library."""

import os
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")


def go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GO111MODULE"] = "on"
    env["GOPROXY"] = "off"
    env["GOSUMDB"] = "off"
    env["GOTOOLCHAIN"] = "local"
    env["CGO_ENABLED"] = "0"
    env["GOCACHE"] = "/tmp/go-build-cache"
    env["GOMODCACHE"] = "/tmp/go-mod-cache"
    return env


def import_paths(text: str) -> list[str]:
    paths: list[str] = []
    in_block = False
    for line in text.splitlines():
        stripped = line.split("//", 1)[0].strip()
        if not in_block and stripped.startswith("import ("):
            in_block = True
            continue
        if in_block:
            if stripped.startswith(")"):
                in_block = False
                continue
            match = re.search(r'"([^"]+)"', stripped)
            if match:
                paths.append(match.group(1))
            continue
        match = re.match(r'import\s+(?:\w+\s+)?"([^"]+)"', stripped)
        if match:
            paths.append(match.group(1))
    return paths


def stdlib_only() -> bool:
    go_mod = REPO / "go.mod"
    if not go_mod.is_file():
        return False
    for line in go_mod.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("require"):
            return False
    go_files = list(REPO.rglob("*.go"))
    if not go_files:
        return False
    for path in go_files:
        for imp in import_paths(path.read_text(encoding="utf-8", errors="replace")):
            if "." in imp or imp.startswith("."):
                return False
    return True


def build_ok() -> bool:
    if not REPO.is_dir() or not stdlib_only():
        return False
    proc = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        env=go_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode == 0


@criterion
def build(workspace: Path) -> bool:
    del workspace
    return build_ok()
