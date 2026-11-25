"""Report-only hard-rule gate: the Go submission cannot launch processes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import no_exec_ok

from rewardkit import criterion


@criterion(description="no subprocess, raw syscall, unsafe, cgo, or nested Go module")
def no_exec(workspace: Path) -> bool:
    return no_exec_ok(workspace)
