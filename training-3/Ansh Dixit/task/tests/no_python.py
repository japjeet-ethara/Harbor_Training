"""Check 2 (weight 1): no .py file anywhere under /workspace/repo AND the build passes.

It only pays when the build passes, so an agent that merely deletes files gets nothing.
It also enforces the "standard library only / no other programs" rules.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rewardkit as rk
from _common import REPO, build_all, build_binary

FORBIDDEN_IMPORT = re.compile(r'"(os/exec|plugin)"')


@rk.criterion(description="no .py files left, build passes, stdlib only, no external programs")
def no_python(workspace: Path) -> bool:
    if any(REPO.rglob("*.py")):
        return False
    if not (build_all() and build_binary("/tmp/no_python_check_bin")):
        return False
    gomod = (REPO / "go.mod").read_text(errors="replace")
    if re.search(r"^\s*(require|replace)\b", gomod, re.M):
        return False
    for f in REPO.rglob("*.go"):
        if FORBIDDEN_IMPORT.search(f.read_text(errors="replace")):
            return False
    return True


rk.no_python()
