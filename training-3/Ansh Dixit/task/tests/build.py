"""Check 1 (weight 1): `go build ./...` passes and the repo root builds a program."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rewardkit as rk
from _common import build_all, build_binary


@rk.criterion(description="go build ./... passes and the root main package builds")
def build_ok(workspace: Path) -> bool:
    return build_all() and build_binary("/tmp/build_check_bin")


rk.build_ok()
