import os
import subprocess
from pathlib import Path

from rewardkit import criterion


def has_go_source(workspace: Path) -> bool:
    """True when the workspace contains a non-test Go file.

    `go build ./...` exits 0 with "matched no packages" when a module has no
    Go files. That must not count as a successful implementation.
    """
    if not workspace.is_dir():
        return False
    return any(
        path.is_file() and path.suffix == ".go" and not path.name.endswith("_test.go")
        for path in workspace.rglob("*")
    )


def go_build(workspace: Path, cache_name: str) -> bool:
    if not has_go_source(workspace):
        return False
    cache = Path("/tmp") / cache_name
    env = os.environ.copy()
    env["GOCACHE"] = str(cache / "cache")
    env["GOMODCACHE"] = str(cache / "mod")
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        env=env,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False
    if b"matched no packages" in result.stderr:
        return False
    return True


@criterion
def build(workspace: Path) -> bool:
    return go_build(workspace, "gocache-build")
