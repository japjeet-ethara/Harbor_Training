"""No .py files remain, and only when the project also builds."""

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
    env["GOCACHE"] = "/tmp/go-build-cache-nopy"
    env["GOMODCACHE"] = "/tmp/go-mod-cache-nopy"
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


def build_ok() -> bool:
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
def no_python(workspace: Path) -> bool:
    del workspace
    if not build_ok():
        return False
    return not any(REPO.rglob("*.py"))
