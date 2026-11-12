"""Build criterion. Weight is applied in reward.toml (this file is `build`)."""

import shutil
import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
# Directory, not a file: `go build -o <dir>/ ./...` writes binaries here
# instead of next to the module, where a leftover titlecase/ directory
# would otherwise collide with the binary name.
OUT_DIR = Path("/tmp/tc_build")


def _go_mod_has_no_require(repo: Path) -> bool:
    gomod = repo / "go.mod"
    if not gomod.is_file():
        return False
    text = gomod.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        code = line.split("//", 1)[0].strip()
        if code.startswith("require"):
            return False
    return True


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _go_build_all(repo: Path) -> bool:
    _remove(Path("/tmp/tc"))
    _remove(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    proc = subprocess.run(
        ["go", "build", "-o", str(OUT_DIR) + "/", "./..."],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.returncode == 0


@criterion
def go_build(workspace: Path) -> float:
    del workspace
    try:
        if not REPO.is_dir():
            return 0.0
        if not _go_mod_has_no_require(REPO):
            return 0.0
        return 1.0 if _go_build_all(REPO) else 0.0
    except Exception:
        return 0.0
