"""Check 2 (weight 1): the Python is gone, the hard rules hold, AND the build passes.

The build requirement stops a do-nothing-but-delete-files attempt from earning points.
"""
import os
import re
import subprocess

import rewardkit as rk

PY_SUFFIXES = (".py",)   # exactly what the instruction forbids


@rk.criterion(description="no Python files remain, rules respected, and the build passes")
def no_python(workspace) -> bool:
    # 1. no Python files anywhere under the repository
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.endswith(PY_SUFFIXES):
                return False

    # 2. hard rules: standard library only, no cgo, no other programs started
    gomod = workspace / "go.mod"
    if not gomod.is_file():
        return False
    if re.search(r"^\s*(require\b|replace\b)", gomod.read_text(errors="replace"), re.M):
        return False
    found_go = False
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if not f.endswith(".go"):
                continue
            found_go = True
            with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            if re.search(r'"os/exec"|import\s+"C"|^\s*"C"\s*$|"plugin"', src, re.M):
                return False
    if not found_go:
        return False

    # 3. the build must pass
    env = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off",
               GOTOOLCHAIN="local", GOCACHE="/tmp/gocache-nopy", CGO_ENABLED="0")
    try:
        r = subprocess.run(["go", "build", "-o", "/dev/null", "./..."], cwd=workspace, env=env,
                           capture_output=True, timeout=240)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0
