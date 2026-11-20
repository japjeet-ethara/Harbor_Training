"""no_exec gate (report-only; weight 0 in reward.toml): the program is pure Go that
starts no other process.

Passes only if the root main package's TRANSITIVE deps (go list -deps .) include none
of os/exec, syscall, unsafe, plugin, runtime/cgo; there is no nested go.mod; and no Go
source contains StartProcess or go:linkname. This closes "embed the Python source and
run it with os/exec", including when os/exec is hidden inside a replaced sub-module.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import no_exec_ok  # noqa: E402

import rewardkit as rk  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="no os/exec, syscall, unsafe, nested module or StartProcess/go:linkname")
def no_exec(workspace: Path) -> bool:
    return no_exec_ok(workspace)


rk.no_exec()
