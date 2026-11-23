import os
import subprocess
from pathlib import Path

from rewardkit import criterion


def has_go_source(workspace: Path) -> bool:
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
    env["GOCACHE"]    = str(cache / "cache")
    env["GOMODCACHE"] = str(cache / "mod")
    env["GOPROXY"]    = "off"
    env["GONOSUMDB"]  = "*"
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


def uses_exec(workspace: Path) -> bool:
    """Return True if any .go file imports os/exec or syscall.

    A program that shells out to python3 (or any other interpreter) must
    import one of these packages.  Rejecting them closes the
    "Python inside" and "interpreter wrapper" cheats without a real Go port.
    """
    forbidden = {"os/exec", "syscall"}
    for path in workspace.rglob("*.go"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pkg in forbidden:
            if f'"{pkg}"' in text:
                return True
    return False


@criterion
def no_python(workspace: Path) -> bool:
    if not has_go_source(workspace):
        return False
    # No .py files anywhere in the workspace
    if any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file()):
        return False
    # No os/exec or syscall imports (blocks interpreter-shelling cheats)
    if uses_exec(workspace):
        return False
    return go_build(workspace, "gocache-no-python")
